from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.recepcion import obtener_sesion
from app.schemas.recepcion import (
    CambioEstadoResultadoEntrada, IncidenciaEntrada, InterpretacionEntrada,
    RecepcionEntrada, ResolucionIncidenciaEntrada, ResultadoEntrada,
    VerificacionPrecintoEntrada,
)
from app.models.recepcion import Incidencia, RecepcionEnvio, ResultadoAnalisis, VerificacionPrecinto
from app.services import recepcion as servicios
from app.services.recepcion import recepcion_pertenece_al_envio_actual
from app.core.recepcion_integracion import listar_envios_despachados
from app.core.laboratorio_gateway import LaboratorioGateway, LaboratorioMock

enrutador = APIRouter(tags=["Módulo 4: recepción y resultados"])


def obtener_laboratorio_gateway() -> LaboratorioGateway:
    return LaboratorioMock()


@enrutador.get("/envios-pendientes")
def listar_envios_pendientes(sesion: Session = Depends(obtener_sesion)):
    recepciones = sesion.scalars(select(RecepcionEnvio)).all()
    recepciones_por_envio = {}
    for recepcion in recepciones:
        recepciones_por_envio.setdefault(recepcion.envio_id, []).append(recepcion)
    incidencias = sesion.scalars(select(Incidencia)).all()
    resultado = []
    for envio in listar_envios_despachados():
        recepciones_envio = [
            recepcion for recepcion in recepciones_por_envio.get(envio.envio_id, [])
            if recepcion_pertenece_al_envio_actual(recepcion, envio)
        ]
        muestras_recibidas = {m for r in recepciones_envio for m in r.muestras_recibidas}
        if set(envio.muestras_ids).issubset(muestras_recibidas):
            continue
        resultado.append({
            "envio_id": envio.envio_id,
            "remito_id": envio.remito_id,
            "fecha_despacho": envio.fecha_despacho,
            "muestras_despachadas": envio.muestras_ids,
            "conservadoras": envio.conservadoras_ids,
            "precintos": envio.precintos,
            "recepciones": recepciones_envio,
            "incidencias": [i for i in incidencias if i.envio_id == envio.envio_id],
        })
    return resultado


@enrutador.post("/recepciones", status_code=status.HTTP_201_CREATED)
def crear_recepcion(datos: RecepcionEntrada, sesion: Session = Depends(obtener_sesion)):
    return servicios.registrar_recepcion(sesion, datos)


@enrutador.get("/recepciones/{recepcion_id}")
def obtener_recepcion(recepcion_id: str, sesion: Session = Depends(obtener_sesion)):
    recepcion = sesion.get(RecepcionEnvio, recepcion_id)
    if not recepcion:
        raise HTTPException(404, "No se encontró la recepción")
    return recepcion


@enrutador.post("/verificaciones-precinto", status_code=status.HTTP_201_CREATED)
def verificar_precinto(datos: VerificacionPrecintoEntrada, sesion: Session = Depends(obtener_sesion)):
    return servicios.registrar_verificacion(sesion, datos)


@enrutador.get("/verificaciones-precinto")
def listar_verificaciones(envio_id: str = Query(min_length=1), sesion: Session = Depends(obtener_sesion)):
    return sesion.scalars(select(VerificacionPrecinto).where(VerificacionPrecinto.envio_id == envio_id)).all()


@enrutador.post("/incidencias", status_code=status.HTTP_201_CREATED)
def registrar_incidencia(datos: IncidenciaEntrada, sesion: Session = Depends(obtener_sesion)):
    incidencia = servicios.crear_incidencia(sesion, datos)
    if incidencia is None:
        raise HTTPException(404, "No se encontró la recepción indicada")
    return incidencia


@enrutador.get("/incidencias")
def listar_incidencias(envio_id: str | None = None, abiertas: bool = False, sesion: Session = Depends(obtener_sesion)):
    consulta = select(Incidencia)
    if envio_id:
        consulta = consulta.where(Incidencia.envio_id == envio_id)
    if abiertas:
        consulta = consulta.where(Incidencia.resuelta_en.is_(None))
    return sesion.scalars(consulta.order_by(Incidencia.fecha.desc())).all()


@enrutador.post("/incidencias/{incidencia_id}/resolver")
def resolver_incidencia(incidencia_id: str, datos: ResolucionIncidenciaEntrada, sesion: Session = Depends(obtener_sesion)):
    incidencia = sesion.get(Incidencia, incidencia_id)
    if not incidencia:
        raise HTTPException(404, "No se encontró la incidencia")
    if incidencia.resuelta_en:
        raise HTTPException(409, "La incidencia ya fue resuelta")
    incidencia.resolucion = datos.resolucion
    incidencia.responsable_resolucion_id = datos.responsable_resolucion_id
    incidencia.resuelta_en = datos.resuelta_en
    sesion.commit()
    sesion.refresh(incidencia)
    return incidencia


@enrutador.post("/resultados", status_code=status.HTTP_201_CREATED)
def cargar_resultado(datos: ResultadoEntrada, sesion: Session = Depends(obtener_sesion)):
    resultado = servicios.registrar_resultado(sesion, datos)
    if resultado is None:
        raise HTTPException(409, "El informe de este análisis ya fue incorporado")
    return resultado


@enrutador.get("/muestras/{muestra_id}/resultados-laboratorio")
def consultar_resultados_laboratorio(
    muestra_id: str,
    escenario: str = Query(default="multiples"),
    sesion: Session = Depends(obtener_sesion),
    gateway: LaboratorioGateway = Depends(obtener_laboratorio_gateway),
):
    return servicios.consultar_resultados_laboratorio(sesion, muestra_id, gateway=gateway, escenario=escenario)


@enrutador.post("/muestras/{muestra_id}/resultados-laboratorio")
def recibir_resultados_laboratorio(
    muestra_id: str,
    escenario: str = Query(default="multiples"),
    sesion: Session = Depends(obtener_sesion),
    gateway: LaboratorioGateway = Depends(obtener_laboratorio_gateway),
):
    return servicios.recibir_resultados_laboratorio(sesion, muestra_id, gateway=gateway, escenario=escenario)


@enrutador.get("/resultados")
def consultar_resultados(orden_id: str | None = None, paciente_id: str | None = None, estado: str | None = None, sesion: Session = Depends(obtener_sesion)):
    consulta = select(ResultadoAnalisis)
    if orden_id:
        consulta = consulta.where(ResultadoAnalisis.orden_id == orden_id)
    if paciente_id:
        consulta = consulta.where(ResultadoAnalisis.paciente_id == paciente_id)
    if estado:
        consulta = consulta.where(ResultadoAnalisis.estado == estado)
    resultados = sesion.scalars(consulta.order_by(ResultadoAnalisis.fecha_recepcion.desc())).all()
    return [resultado for resultado in resultados if servicios.resultado_es_vigente(sesion, resultado)]


@enrutador.patch("/resultados/{resultado_id}/estado")
def cambiar_estado_resultado(resultado_id: str, datos: CambioEstadoResultadoEntrada, sesion: Session = Depends(obtener_sesion)):
    resultado = sesion.get(ResultadoAnalisis, resultado_id)
    if not resultado:
        raise HTTPException(404, "No se encontró el resultado")
    return servicios.actualizar_estado_resultado(sesion, resultado, datos.estado)


@enrutador.patch("/resultados/{resultado_id}/interpretacion")
def registrar_interpretacion(resultado_id: str, datos: InterpretacionEntrada, sesion: Session = Depends(obtener_sesion)):
    resultado = sesion.get(ResultadoAnalisis, resultado_id)
    if not resultado:
        raise HTTPException(404, "No se encontró el resultado")
    return servicios.agregar_interpretacion(sesion, resultado, datos.interpretacion_clinica)
