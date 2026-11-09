from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.orden_analisis import (
    AsociarMuestraAnalisisCreate,
    ConfigurarCompatibilidadCreate,
    DetalleOrdenAnalisisRead,
    HistorialMuestraRead,
    HistorialOrdenAnalisisRead,
    MuestraCreate,
    MuestraEstadoUpdate,
    MuestraRead,
    OrdenAnalisisRead,
    OrdenEstadoUpdate,
    ResultadoAsociacionRead,
    SeguimientoOrdenMuestrasRead,
    SolicitudAnalisisCreate,
    TipoAnalisisCreate,
    TipoAnalisisRead,
    TipoMuestraCreate,
    TipoMuestraRead,
)
from app.services.orden_analisis_service import OrdenAnalisisService

router = APIRouter(prefix="/api/v1", tags=["Órdenes y análisis"])


def get_service(db: Session = Depends(get_db)) -> OrdenAnalisisService:
    return OrdenAnalisisService(db)


# --- Catálogo de Tipos de Análisis ---

@router.post(
    "/tipos-analisis",
    response_model=TipoAnalisisRead,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un tipo de análisis en el catálogo",
)
def create_tipo_analisis(
    payload: TipoAnalisisCreate,
    service: OrdenAnalisisService = Depends(get_service),
):
    return service.crear_tipo_analisis(payload)


@router.get(
    "/tipos-analisis",
    response_model=list[TipoAnalisisRead],
    summary="Listar tipos de análisis disponibles",
)
def list_tipos_analisis(
    only_active: bool = Query(default=True, description="Filtrar solo los tipos activos"),
    service: OrdenAnalisisService = Depends(get_service),
):
    return service.listar_tipos_analisis(only_active=only_active)


@router.post(
    "/tipos-analisis/{tipo_analisis_id}/compatibilidad",
    response_model=TipoAnalisisRead,
    summary="US-09: Configurar qué tipos de muestra son compatibles con un tipo de análisis",
)
def configurar_compatibilidad(
    tipo_analisis_id: int,
    payload: ConfigurarCompatibilidadCreate,
    service: OrdenAnalisisService = Depends(get_service),
):
    return service.configurar_compatibilidad(tipo_analisis_id, payload)


# --- Crear y Solicitar Orden de Análisis ---

@router.post(
    "/ordenes-analisis/solicitar",
    response_model=OrdenAnalisisRead,
    status_code=status.HTTP_201_CREATED,
    summary="US-06: Solicitar uno o varios análisis clínicos para una consulta",
)
def solicitar_analisis(
    payload: SolicitudAnalisisCreate,
    service: OrdenAnalisisService = Depends(get_service),
):
    return service.solicitar_analisis(payload)


@router.post(
    "/ordenes-analisis",
    response_model=OrdenAnalisisRead,
    status_code=status.HTTP_201_CREATED,
    summary="US-07: Crear formalmente una orden de análisis para enviar al laboratorio",
)
def crear_orden_analisis(
    payload: SolicitudAnalisisCreate,
    service: OrdenAnalisisService = Depends(get_service),
):
    return service.solicitar_analisis(payload)


@router.get(
    "/ordenes-analisis",
    response_model=list[OrdenAnalisisRead],
    summary="Listar órdenes de análisis",
)
def list_ordenes_analisis(
    consulta_id: int | None = Query(default=None, description="Filtrar por consulta médica"),
    service: OrdenAnalisisService = Depends(get_service),
):
    return service.listar_ordenes(consulta_id=consulta_id)


@router.get(
    "/ordenes-analisis/{orden_id}",
    response_model=OrdenAnalisisRead,
    summary="US-07: Obtener detalle completo de una orden de análisis (paciente, solicitante, análisis)",
)
def get_orden_analisis(
    orden_id: int,
    service: OrdenAnalisisService = Depends(get_service),
):
    return service.obtener_orden_por_id(orden_id)


# --- Formalización, Cambios de Estado e Historial ---

@router.patch(
    "/ordenes-analisis/{orden_id}/estado",
    response_model=OrdenAnalisisRead,
    summary="US-07: Actualizar o formalizar el estado de la orden (ej: pasar a en_preparacion)",
)
def update_estado_orden(
    orden_id: int,
    payload: OrdenEstadoUpdate,
    service: OrdenAnalisisService = Depends(get_service),
):
    return service.actualizar_estado_orden(orden_id, payload)


@router.get(
    "/ordenes-analisis/{orden_id}/historial",
    response_model=list[HistorialOrdenAnalisisRead],
    summary="US-07: Consultar el historial de trazabilidad y cambios de estado de una orden",
)
def get_historial_orden(
    orden_id: int,
    service: OrdenAnalisisService = Depends(get_service),
):
    return service.obtener_historial_orden(orden_id)


@router.get(
    "/consultas/{consulta_id}/analisis",
    response_model=list[OrdenAnalisisRead],
    summary="Consultar análisis solicitados para una consulta médica específica",
)
def list_analisis_by_consulta(
    consulta_id: int,
    service: OrdenAnalisisService = Depends(get_service),
):
    return service.listar_ordenes(consulta_id=consulta_id)


# --- Tipos de Muestra ---

@router.post(
    "/tipos-muestra",
    response_model=TipoMuestraRead,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un tipo de material biológico en el catálogo",
)
def create_tipo_muestra(
    payload: TipoMuestraCreate,
    service: OrdenAnalisisService = Depends(get_service),
):
    return service.crear_tipo_muestra(payload)


@router.get(
    "/tipos-muestra",
    response_model=list[TipoMuestraRead],
    summary="Listar tipos de muestra disponibles",
)
def list_tipos_muestra(
    only_active: bool = Query(default=True, description="Filtrar solo los tipos activos"),
    service: OrdenAnalisisService = Depends(get_service),
):
    return service.listar_tipos_muestra(only_active=only_active)


# --- Muestras Biológicas ---

@router.post(
    "/muestras",
    response_model=MuestraRead,
    status_code=status.HTTP_201_CREATED,
    summary="US-08: Registrar la extracción de una muestra biológica vinculada a una orden",
)
def registrar_extraccion_muestra(
    payload: MuestraCreate,
    service: OrdenAnalisisService = Depends(get_service),
):
    return service.registrar_extraccion_muestra(payload)


@router.get(
    "/muestras/{muestra_id}",
    response_model=MuestraRead,
    summary="US-08: Obtener el detalle y trazabilidad de una muestra biológica",
)
def get_muestra(
    muestra_id: int,
    service: OrdenAnalisisService = Depends(get_service),
):
    return service.obtener_muestra_por_id(muestra_id)


@router.get(
    "/ordenes-analisis/{orden_id}/muestras",
    response_model=list[MuestraRead],
    summary="US-08: Listar todas las muestras biológicas vinculadas a una orden de análisis",
)
def list_muestras_por_orden(
    orden_id: int,
    service: OrdenAnalisisService = Depends(get_service),
):
    return service.listar_muestras_por_orden(orden_id)


# --- Asociación Muestras con Análisis ---

@router.post(
    "/ordenes-analisis/{orden_id}/asociar-muestra",
    response_model=ResultadoAsociacionRead,
    summary="US-09: Vincular una muestra con uno o varios análisis que puede satisfacer",
)
def asociar_muestra_con_analisis(
    orden_id: int,
    payload: AsociarMuestraAnalisisCreate,
    service: OrdenAnalisisService = Depends(get_service),
):
    return service.asociar_muestra_con_analisis(orden_id, payload)


@router.get(
    "/ordenes-analisis/{orden_id}/analisis-pendientes",
    response_model=list[DetalleOrdenAnalisisRead],
    summary="US-09: Identificar análisis de la orden que todavía no cuentan con una muestra adecuada asignada",
)
def list_analisis_pendientes_muestra(
    orden_id: int,
    service: OrdenAnalisisService = Depends(get_service),
):
    return service.listar_analisis_pendientes_muestra(orden_id)


# --- Estado de Orden y Muestras ---

@router.patch(
    "/muestras/{muestra_id}/estado",
    response_model=MuestraRead,
    summary="US-10: Actualizar el estado de una muestra (registrada, pendiente_preparacion, lista_para_envio, enviada, con_inconveniente)",
)
def update_estado_muestra(
    muestra_id: int,
    payload: MuestraEstadoUpdate,
    service: OrdenAnalisisService = Depends(get_service),
):
    return service.actualizar_estado_muestra(muestra_id, payload)


@router.get(
    "/muestras/{muestra_id}/historial",
    response_model=list[HistorialMuestraRead],
    summary="US-10: Consultar el historial cronológico de cambios de estado de una muestra",
)
def get_historial_muestra(
    muestra_id: int,
    service: OrdenAnalisisService = Depends(get_service),
):
    return service.obtener_historial_muestra(muestra_id)


@router.get(
    "/ordenes-analisis/{orden_id}/seguimiento",
    response_model=SeguimientoOrdenMuestrasRead,
    summary="US-10: Consultar el estado consolidado de la orden y sus muestras (listas para enviar vs con inconvenientes)",
)
def get_seguimiento_orden_y_muestras(
    orden_id: int,
    service: OrdenAnalisisService = Depends(get_service),
):
    return service.consultar_estado_orden_y_muestras(orden_id)



