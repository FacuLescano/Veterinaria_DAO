from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.recepcion import Incidencia, RecepcionEnvio, ResultadoAnalisis, VerificacionPrecinto
from app.models.envio import Envio
from app.models.orden_analisis import DetalleOrdenAnalisis, Muestra, OrdenAnalisis
from app.observers.muestra import RecepcionMuestra, publicar_recepcion_muestra
from app.observers.resultados import ResultadosRegistrados, resultados_analisis
import logging

logger = logging.getLogger(__name__)


def registrar_recepcion(sesion: Session, datos):
    envio = sesion.get(Envio, int(datos.envio_id))
    if not envio or envio.estado != "despachado":
        raise HTTPException(404, "No se encontró un envío despachado con ese identificador")
    despachadas_reales = {str(m.id) for m in envio.muestras}
    despachadas = set(datos.muestras_despachadas)
    recibidas = set(datos.muestras_recibidas)
    if despachadas != despachadas_reales or not recibidas.issubset(despachadas_reales):
        raise HTTPException(422, "Las muestras informadas no coinciden con el contenido del envío")
    if sesion.scalar(select(RecepcionEnvio.id).where(RecepcionEnvio.envio_id == datos.envio_id)):
        raise HTTPException(409, "Este envío ya tiene una recepción registrada")
    estado = "completa" if despachadas == recibidas else "parcial"
    recepcion = RecepcionEnvio(**datos.model_dump(), estado=estado)
    sesion.add(recepcion)
    sesion.flush()
    discrepancias = [("muestra_faltante", elemento) for elemento in despachadas - recibidas]
    discrepancias += [("muestra_sobrante", elemento) for elemento in recibidas - despachadas]
    for tipo, muestra_id in discrepancias:
        sesion.add(Incidencia(
            recepcion_id=recepcion.id, envio_id=recepcion.envio_id, tipo=tipo,
            descripcion=f"Muestra {muestra_id} { 'faltante' if tipo == 'muestra_faltante' else 'sobrante' } al contrastar la recepción con el despacho.",
            fecha=recepcion.fecha_recepcion, responsable_id=recepcion.responsable_id,
            muestra_id=muestra_id,
        ))
    for muestra in envio.muestras:
        try:
            if str(muestra.id) in recibidas:
                if muestra.estado == "enviada":
                    muestra.recibir(responsable=datos.responsable_id, motivo="Recepción registrada en el laboratorio", fecha_evento=datos.fecha_recepcion)
            elif muestra.estado not in {"rechazada", "con_inconveniente"}:
                muestra.transicionar_a_estado("con_inconveniente", "Muestra faltante en recepción", responsable=datos.responsable_id)
        except (ValueError, AttributeError):
            pass
    for conservadora in envio.conservadoras:
        conservadora.disponible = True
    sesion.commit()
    sesion.refresh(recepcion)
    return recepcion


def registrar_verificacion(sesion: Session, datos):
    envio = sesion.get(Envio, int(datos.envio_id))
    if not envio or envio.estado != "despachado":
        raise HTTPException(404, "No se encontró un envío despachado con ese identificador")
    verificacion = VerificacionPrecinto(**datos.model_dump())
    sesion.add(verificacion)
    anomalia_codigo = datos.codigo_esperado is not None and datos.codigo_observado != datos.codigo_esperado
    if datos.estado != "integro" or anomalia_codigo:
        descripcion = datos.observaciones or "Se detectó una anomalía al verificar el precinto."
        if anomalia_codigo:
            descripcion += f" Código esperado: {datos.codigo_esperado}; observado: {datos.codigo_observado or 'ausente'}."
        sesion.add(Incidencia(
            envio_id=datos.envio_id, tipo="precinto", descripcion=descripcion,
            fecha=datos.fecha_verificacion, responsable_id=datos.responsable_id,
            precinto_id=datos.precinto_id,
        ))
        motivo = f"Rechazo de recepción por precinto: {descripcion}"
        for muestra in envio.muestras:
            if muestra.estado == "enviada":
                muestra.transicionar_a_estado("con_inconveniente", motivo, responsable=datos.responsable_id)
    sesion.commit()
    sesion.refresh(verificacion)
    resultado_recepcion = "aceptada" if datos.estado == "integro" and not anomalia_codigo else "rechazada"
    try:
        for muestra in envio.muestras:
            orden = muestra.orden
            if not orden:
                continue
            mascota = orden.consulta.pet if orden.consulta else None
            condicion = datos.estado
            if anomalia_codigo:
                condicion = f"{datos.estado}; código observado no coincide"
            estado_muestra_recepcion = "recibida" if resultado_recepcion == "aceptada" else "rechazada"
            publicar_recepcion_muestra(RecepcionMuestra(
                muestra_id=muestra.id,
                codigo_etiqueta=muestra.codigo_etiqueta,
                orden_id=orden.id,
                veterinario_id=orden.veterinario_id,
                mascota_nombre=mascota.name if mascota else None,
                resultado=resultado_recepcion,
                condicion_precinto=condicion,
                ocurrido_en=datos.fecha_verificacion,
                mensaje=(
                    f"Muestra {muestra.codigo_etiqueta} ({mascota.name if mascota else 'mascota sin identificar'}): "
                    f"precinto {condicion}; muestra {estado_muestra_recepcion}."
                ),
            ), sesion)
        sesion.commit()
    except Exception:
        sesion.rollback()
        logger.exception("No se pudieron persistir las notificaciones de recepción del envío %s", datos.envio_id)
    return verificacion


def crear_incidencia(sesion: Session, datos):
    valores = datos.model_dump()
    recepcion_id = valores.pop("recepcion_id")
    if recepcion_id and not sesion.get(RecepcionEnvio, recepcion_id):
        return None
    incidencia = Incidencia(**valores, recepcion_id=recepcion_id)
    sesion.add(incidencia)
    sesion.commit()
    sesion.refresh(incidencia)
    return incidencia


def registrar_resultado(sesion: Session, datos):
    identidad_resultado = [
        ResultadoAnalisis.orden_id == datos.orden_id,
        ResultadoAnalisis.detalle_orden_id == datos.detalle_orden_id,
    ]
    if datos.informe_nombre:
        identidad_resultado.append(ResultadoAnalisis.informe_nombre == datos.informe_nombre)
    else:
        identidad_resultado.extend([
            ResultadoAnalisis.informe_nombre.is_(None),
            ResultadoAnalisis.paciente_id == datos.paciente_id,
            ResultadoAnalisis.fecha_recepcion == datos.fecha_recepcion,
            ResultadoAnalisis.procedencia == datos.procedencia,
        ])
    duplicado = sesion.scalar(select(ResultadoAnalisis.id).where(*identidad_resultado))
    if duplicado:
        return None
    resultado = ResultadoAnalisis(**datos.model_dump())
    sesion.add(resultado)
    detalle = sesion.get(DetalleOrdenAnalisis, int(datos.detalle_orden_id))
    if not detalle or detalle.orden_id != int(datos.orden_id):
        raise HTTPException(404, "No se encontró el análisis de la orden indicada")
    orden = sesion.get(OrdenAnalisis, detalle.orden_id)
    paciente_id_real = orden.consulta.pet_id if orden and orden.consulta else None
    if paciente_id_real is None or str(paciente_id_real) != str(datos.paciente_id):
        raise HTTPException(422, "El paciente informado no corresponde a la orden de análisis")
    detalle.estado = "resultado_listo"
    orden = sesion.get(OrdenAnalisis, detalle.orden_id)
    if orden and all(d.estado == "resultado_listo" for d in orden.detalles):
        orden.estado = "con_resultados"
    if datos.muestra_id:
        muestra = sesion.get(Muestra, int(datos.muestra_id))
        if muestra and muestra.estado == "recibida":
            muestra.registrar_analisis(datos.informe_nombre or "resultado", responsable=datos.registrado_por, motivo="Resultado de laboratorio registrado", fecha_evento=datos.fecha_recepcion)
    sesion.commit()
    sesion.refresh(resultado)
    try:
        resultados_analisis.notificar(
            ResultadosRegistrados(resultado_id=str(resultado.id), paciente_id=str(resultado.paciente_id)),
            sesion,
        )
    except Exception:
        logger.exception("No se pudo publicar el evento de resultados %s", resultado.id)
    return resultado


def actualizar_estado_resultado(sesion: Session, resultado: ResultadoAnalisis, estado: str):
    resultado.estado = estado
    sesion.commit()
    sesion.refresh(resultado)
    return resultado


def agregar_interpretacion(sesion: Session, resultado: ResultadoAnalisis, interpretacion: str):
    resultado.interpretacion_clinica = interpretacion
    sesion.commit()
    sesion.refresh(resultado)
    return resultado
