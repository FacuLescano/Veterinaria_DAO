from sqlalchemy import select
from sqlalchemy.orm import Session

from vet_back.app.models.recepcion import Incidencia, RecepcionEnvio, ResultadoAnalisis, VerificacionPrecinto


def registrar_recepcion(sesion: Session, datos):
    despachadas = set(datos.muestras_despachadas)
    recibidas = set(datos.muestras_recibidas)
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
    sesion.commit()
    sesion.refresh(recepcion)
    return recepcion


def registrar_verificacion(sesion: Session, datos):
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
