from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.orden_analisis import (
    OrdenAnalisisRead,
    SolicitudAnalisisCreate,
    TipoAnalisisCreate,
    TipoAnalisisRead,
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


# --- US-06: Solicitar Análisis ---

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
    summary="Obtener detalle de una orden de análisis por ID",
)
def get_orden_analisis(
    orden_id: int,
    service: OrdenAnalisisService = Depends(get_service),
):
    return service.obtener_orden_por_id(orden_id)


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
