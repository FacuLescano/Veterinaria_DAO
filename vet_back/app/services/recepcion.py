from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.recepcion import Incidencia, RecepcionEnvio, ResultadoAnalisis, VerificacionPrecinto
from app.models.envio import Envio
from app.models.orden_analisis import AsociacionDetalleMuestra, DetalleOrdenAnalisis, Muestra, OrdenAnalisis
from app.core.laboratorio_gateway import LaboratorioMock, RespuestaLaboratorio
from app.observers.muestra import RecepcionMuestra, publicar_recepcion_muestra
from app.observers.resultados import ResultadoAnalisisRegistrado, ResultadosRegistrados, resultados_analisis
import logging

logger = logging.getLogger(__name__)


def normalizar_fecha_utc(fecha: datetime) -> datetime:
    """Normaliza fechas naive de SQLite y fechas con zona para poder compararlas."""
    if fecha.tzinfo is None:
        return fecha.replace(tzinfo=timezone.utc)
    return fecha.astimezone(timezone.utc)


def recepcion_pertenece_al_envio_actual(recepcion: RecepcionEnvio, envio: Envio) -> bool:
    """Ignora recepciones históricas cuyo ID fue reutilizado por un despacho nuevo."""
    return bool(
        envio.fecha_despacho
        and normalizar_fecha_utc(recepcion.fecha_recepcion) >= normalizar_fecha_utc(envio.fecha_despacho)
    )


def verificacion_actual_del_envio(sesion: Session, envio: Envio):
    """Devuelve la última verificación registrada desde el despacho vigente."""
    if not envio.fecha_despacho:
        return None
    verificaciones = sesion.scalars(
        select(VerificacionPrecinto).where(VerificacionPrecinto.envio_id == str(envio.id))
    ).all()
    actuales = [
        verificacion for verificacion in verificaciones
        if normalizar_fecha_utc(verificacion.fecha_verificacion) >= normalizar_fecha_utc(envio.fecha_despacho)
    ]
    return max(actuales, key=lambda verificacion: normalizar_fecha_utc(verificacion.fecha_verificacion), default=None)


def resultado_es_vigente(sesion: Session, resultado: ResultadoAnalisis) -> bool:
    """Evita atribuir a órdenes o muestras actuales resultados de IDs reutilizados."""
    try:
        orden = sesion.get(OrdenAnalisis, int(resultado.orden_id))
        detalle = sesion.get(DetalleOrdenAnalisis, int(resultado.detalle_orden_id))
    except (TypeError, ValueError):
        return False
    if not orden or not detalle or detalle.orden_id != orden.id or not orden.created_at:
        return False
    if normalizar_fecha_utc(resultado.fecha_recepcion) < normalizar_fecha_utc(orden.created_at):
        return False
    if resultado.muestra_id:
        try:
            muestra = sesion.get(Muestra, int(resultado.muestra_id))
        except (TypeError, ValueError):
            return False
        if not muestra or muestra.orden_id != orden.id or not muestra.fecha_extraccion:
            return False
        if normalizar_fecha_utc(resultado.fecha_recepcion) < normalizar_fecha_utc(muestra.fecha_extraccion):
            return False
    return True


def resultados_existentes_para_muestra(sesion: Session, muestra: Muestra) -> list[ResultadoAnalisis]:
    """Busca resultados actuales asociados a la muestra y a sus análisis."""
    detalle_ids = {str(asociacion.detalle_id) for asociacion in muestra.asociaciones_detalles}
    if not muestra.orden_id or not detalle_ids:
        return []
    candidatos = sesion.scalars(
        select(ResultadoAnalisis).where(
            ResultadoAnalisis.orden_id == str(muestra.orden_id),
            ResultadoAnalisis.detalle_orden_id.in_(detalle_ids),
            (ResultadoAnalisis.muestra_id == str(muestra.id)) | ResultadoAnalisis.muestra_id.is_(None),
        )
    ).all()
    resultados = []
    for resultado in candidatos:
        if not resultado_es_vigente(sesion, resultado):
            continue
        if resultado.muestra_id:
            resultados.append(resultado)
            continue
        detalle_id = int(resultado.detalle_orden_id)
        otras_asociaciones = sesion.scalars(
            select(AsociacionDetalleMuestra.muestra_id).where(
                AsociacionDetalleMuestra.detalle_id == detalle_id
            ).limit(2)
        ).all()
        if len(otras_asociaciones) == 1 and str(otras_asociaciones[0]) == str(muestra.id):
            resultados.append(resultado)
    return resultados


def registrar_recepcion(sesion: Session, datos):
    envio = sesion.get(Envio, int(datos.envio_id))
    if not envio or envio.estado != "despachado":
        raise HTTPException(404, "No se encontró un envío despachado con ese identificador")
    if not envio.fecha_despacho:
        raise HTTPException(409, "El envío todavía no tiene una fecha de despacho registrada")
    if normalizar_fecha_utc(datos.fecha_recepcion) < normalizar_fecha_utc(envio.fecha_despacho):
        raise HTTPException(422, "La fecha de recepción no puede ser anterior al despacho")
    despachadas_reales = {str(m.id) for m in envio.muestras}
    despachadas = set(datos.muestras_despachadas)
    recibidas = set(datos.muestras_recibidas)
    if despachadas != despachadas_reales or not recibidas.issubset(despachadas_reales):
        raise HTTPException(422, "Las muestras informadas no coinciden con el contenido del envío")
    verificaciones = verificacion_actual_del_envio(sesion, envio)
    if not verificaciones:
        raise HTTPException(409, "Registrá la verificación del precinto antes de registrar la recepción")
    recepciones_actuales = sesion.scalars(
        select(RecepcionEnvio).where(RecepcionEnvio.envio_id == datos.envio_id)
    ).all()
    if any(recepcion_pertenece_al_envio_actual(recepcion, envio) for recepcion in recepciones_actuales):
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
    if not envio.fecha_despacho or normalizar_fecha_utc(datos.fecha_verificacion) < normalizar_fecha_utc(envio.fecha_despacho):
        raise HTTPException(422, "La verificación no puede ser anterior al despacho vigente")
    recepciones = sesion.scalars(
        select(RecepcionEnvio).where(RecepcionEnvio.envio_id == datos.envio_id)
    ).all()
    if any(recepcion_pertenece_al_envio_actual(recepcion, envio) for recepcion in recepciones):
        raise HTTPException(409, "Este envío ya tiene una recepción registrada")
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
    try:
        detalle = sesion.get(DetalleOrdenAnalisis, int(datos.detalle_orden_id))
        orden = sesion.get(OrdenAnalisis, int(datos.orden_id))
    except (TypeError, ValueError):
        detalle = orden = None
    if not detalle or not orden or detalle.orden_id != orden.id:
        raise HTTPException(404, "No se encontró el análisis de la orden indicada")
    paciente_id_real = orden.consulta.pet_id if orden.consulta else None
    if paciente_id_real is None or str(paciente_id_real) != str(datos.paciente_id):
        raise HTTPException(422, "El paciente informado no corresponde a la orden de análisis")
    muestra_id = str(datos.muestra_id) if datos.muestra_id else None
    identidad_resultado = [
        ResultadoAnalisis.orden_id == datos.orden_id,
        ResultadoAnalisis.detalle_orden_id == datos.detalle_orden_id,
        ResultadoAnalisis.muestra_id == muestra_id,
    ]
    posibles_duplicados = sesion.scalars(select(ResultadoAnalisis).where(*identidad_resultado)).all()
    if any(resultado_es_vigente(sesion, existente) for existente in posibles_duplicados):
        return None
    resultado = ResultadoAnalisis(**datos.model_dump())
    sesion.add(resultado)
    detalle.estado = "resultado_listo"
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


def _consultar_gateway(sesion: Session, muestra_id: str, gateway, escenario: str) -> tuple[Muestra, RespuestaLaboratorio]:
    try:
        muestra = sesion.get(Muestra, int(muestra_id))
    except (TypeError, ValueError):
        muestra = None
    if not muestra:
        raise HTTPException(404, "No se encontró la muestra")
    analisis = [
        {"detalle_id": str(asociacion.detalle.id), "nombre": asociacion.detalle.tipo_analisis.nombre}
        for asociacion in muestra.asociaciones_detalles
    ]
    if not analisis:
        raise HTTPException(422, "La muestra no tiene análisis asociados")
    try:
        respuesta = gateway.consultar_resultados(str(muestra.id), analisis, escenario)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    return muestra, respuesta


def _validar_respuesta_laboratorio(muestra: Muestra, respuesta: RespuestaLaboratorio):
    if respuesta.muestra_id != str(muestra.id):
        raise HTTPException(422, "La respuesta del laboratorio no corresponde a la muestra solicitada")
    if respuesta.estado == "sin_resultados":
        return {"estado": "sin_resultados", "muestra_id": str(muestra.id), "mensaje": respuesta.mensaje, "resultados": []}
    if respuesta.estado == "pendiente":
        return {"estado": "pendiente", "muestra_id": str(muestra.id), "mensaje": respuesta.mensaje, "resultados": []}
    if respuesta.estado != "disponible":
        raise HTTPException(422, "La respuesta del laboratorio no corresponde a la muestra solicitada")
    if not respuesta.resultados:
        raise HTTPException(422, "La respuesta del laboratorio no contiene resultados")
    esperados = {str(asociacion.detalle.id) for asociacion in muestra.asociaciones_detalles}
    recibidos = [str(r.detalle_id) for r in respuesta.resultados]
    if len(set(recibidos)) != len(recibidos) or set(recibidos) != esperados:
        raise HTTPException(422, "Los análisis recibidos no coinciden con los asociados a la muestra")
    for resultado in respuesta.resultados:
        if not isinstance(resultado.valores, list) or not resultado.valores or any(
            not isinstance(v, dict) or not all(isinstance(v.get(campo), str) and v[campo].strip() for campo in ("parametro", "valor", "unidad", "rangoReferencia"))
            for v in resultado.valores
        ) or not isinstance(resultado.conclusion, str) or not resultado.conclusion.strip():
            raise HTTPException(422, "La respuesta del laboratorio contiene datos incompletos")
    return {"estado": "disponible", "muestra_id": str(muestra.id), "mensaje": respuesta.mensaje, "resultados": respuesta.resultados}


def consultar_resultados_laboratorio(sesion: Session, muestra_id: str, gateway=None, escenario: str = "multiples"):
    """Consulta la dependencia externa y valida identidad y estructura de su respuesta."""
    try:
        muestra_existente = sesion.get(Muestra, int(muestra_id))
    except (TypeError, ValueError):
        muestra_existente = None
    if not muestra_existente:
        raise HTTPException(404, "No se encontró la muestra")
    resultados_existentes = resultados_existentes_para_muestra(sesion, muestra_existente)
    if resultados_existentes:
        return {
            "estado": "ya_registrado",
            "muestra_id": str(muestra_existente.id),
            "mensaje": "Esta muestra ya tiene resultados registrados para sus análisis.",
            "resultados": resultados_existentes,
        }
    muestra, respuesta = _consultar_gateway(sesion, muestra_id, gateway or LaboratorioMock(), escenario)
    return _validar_respuesta_laboratorio(muestra, respuesta)


def recibir_resultados_laboratorio(sesion: Session, muestra_id: str, gateway=None, escenario: str = "multiples"):
    """Valida y persiste todos los resultados de una muestra en una sola operación."""
    try:
        muestra = sesion.get(Muestra, int(muestra_id))
    except (TypeError, ValueError):
        muestra = None
    if not muestra:
        raise HTTPException(404, "No se encontró la muestra")
    if muestra.estado != "recibida":
        raise HTTPException(409, "Solo se pueden recibir resultados para muestras recibidas")
    if resultados_existentes_para_muestra(sesion, muestra):
        raise HTTPException(409, "Esta muestra ya tiene resultados registrados; no se consultó nuevamente al laboratorio")
    muestra, respuesta_gateway = _consultar_gateway(sesion, muestra_id, gateway or LaboratorioMock(), escenario)
    consulta = _validar_respuesta_laboratorio(muestra, respuesta_gateway)
    if consulta["estado"] != "disponible":
        return consulta
    orden = muestra.orden
    paciente_id = orden.consulta.pet_id if orden and orden.consulta else None
    if paciente_id is None:
        raise HTTPException(422, "No se pudo resolver el paciente asociado a la muestra")
    detalles = {str(a.detalle.id): a.detalle for a in muestra.asociaciones_detalles}
    fecha = respuesta_gateway.fecha_recepcion
    creados = []
    try:
        for externo in consulta["resultados"]:
            detalle = detalles[str(externo.detalle_id)]
            informe_nombre = f"MOCK-{muestra.id}-{detalle.id}.json"
            resultado = ResultadoAnalisis(
                orden_id=str(orden.id), detalle_orden_id=str(detalle.id), muestra_id=str(muestra.id),
                paciente_id=str(paciente_id), fecha_recepcion=fecha, procedencia="Laboratorio externo simulado",
                estado="recibido", datos={"valores": externo.valores, "conclusionDiagnostica": externo.conclusion},
                informe_nombre=informe_nombre, registrado_por="LaboratorioMock",
            )
            sesion.add(resultado)
            detalle.estado = "resultado_listo"
            creados.append(resultado)
        muestra.registrar_analisis(
            f"mock:{muestra.id}", responsable="Integración de resultados",
            motivo="Resultados externos recibidos", fecha_evento=fecha,
        )
        if all(d.estado == "resultado_listo" for d in orden.detalles):
            orden.estado = "con_resultados"
        sesion.flush()
        sesion.commit()
        for resultado in creados:
            sesion.refresh(resultado)
    except Exception:
        sesion.rollback()
        raise
    try:
        resultados_analisis.notificar(
            ResultadoAnalisisRegistrado(resultado_ids=tuple(str(r.id) for r in creados), paciente_id=str(paciente_id)), sesion
        )
    except Exception:
        logger.exception("No se pudo publicar el evento de resultados de la muestra %s", muestra.id)
    return {"estado": "registrado", "muestra_id": str(muestra.id), "resultados": creados}


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
