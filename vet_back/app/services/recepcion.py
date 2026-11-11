from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.recepcion import Incidencia, RecepcionEnvio, ResultadoAnalisis, VerificacionPrecinto
from app.models.envio import Envio
from app.models.orden_analisis import DetalleOrdenAnalisis, Muestra, OrdenAnalisis


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
        motivo = descripcion
        for muestra in envio.muestras:
            if muestra.estado == "enviada":
                muestra.transicionar_a_estado("con_inconveniente", motivo, responsable=datos.responsable_id)
    sesion.commit()
    sesion.refresh(verificacion)
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
    duplicado = sesion.scalar(select(ResultadoAnalisis.id).where(
        ResultadoAnalisis.orden_id == datos.orden_id,
        ResultadoAnalisis.detalle_orden_id == datos.detalle_orden_id,
        ResultadoAnalisis.informe_nombre == datos.informe_nombre,
    )) if datos.informe_nombre else None
    if duplicado:
        return None
    resultado = ResultadoAnalisis(**datos.model_dump())
    sesion.add(resultado)
    detalle = sesion.get(DetalleOrdenAnalisis, int(datos.detalle_orden_id))
    if not detalle or detalle.orden_id != int(datos.orden_id):
        raise HTTPException(404, "No se encontró el análisis de la orden indicada")
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
