from fastapi import APIRouter, Depends, status
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.envio import (
    ConservadoraCreate,
    ConservadoraRead,
    DespachoCreate,
    EnvioCreate,
    EnvioRead,
    IncidenciaTransporteCreate,
    PrecintoCreate,
    RegistroTemperaturaCreate,
    RemitoRead,
    VerificacionPrecintoCreate,
)
from app.services.envio_service import EnvioService


router = APIRouter(prefix="/api/v1", tags=["Preparación, despacho y trazabilidad"])


def get_service(db: Session = Depends(get_db)) -> EnvioService:
    return EnvioService(db)


@router.post(
    "/conservadoras",
    response_model=ConservadoraRead,
    status_code=status.HTTP_201_CREATED,
    summary="US-11: Registrar e identificar una conservadora",
)
def registrar_conservadora(
    payload: ConservadoraCreate,
    service: EnvioService = Depends(get_service),
):
    return service.registrar_conservadora(payload)


@router.get("/conservadoras", response_model=list[ConservadoraRead], summary="Listar conservadoras")
def listar_conservadoras(service: EnvioService = Depends(get_service)):
    return service.listar_conservadoras()


@router.post(
    "/envios",
    response_model=EnvioRead,
    status_code=status.HTTP_201_CREATED,
    summary="US-13: Preparar un envío y asignar muestras a conservadoras",
)
def preparar_envio(payload: EnvioCreate, service: EnvioService = Depends(get_service)):
    return service.crear_envio(payload)


@router.post(
    "/envios/{envio_id}/precintos",
    response_model=EnvioRead,
    status_code=status.HTTP_201_CREATED,
    summary="US-12: Colocar y registrar el precinto sanitario de una conservadora",
)
def registrar_precinto(
    envio_id: int,
    payload: PrecintoCreate,
    service: EnvioService = Depends(get_service),
):
    return service.registrar_precinto(envio_id, payload)


@router.post(
    "/envios/{envio_id}/verificaciones-precinto",
    response_model=EnvioRead,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar verificación trazable de un precinto sanitario",
)
def verificar_precinto(
    envio_id: int,
    payload: VerificacionPrecintoCreate,
    service: EnvioService = Depends(get_service),
):
    return service.verificar_precinto(envio_id, payload)


@router.post(
    "/envios/{envio_id}/despachar",
    response_model=EnvioRead,
    summary="US-14/15: Emitir el remito y registrar la salida del envío",
)
def despachar_envio(
    envio_id: int,
    payload: DespachoCreate,
    service: EnvioService = Depends(get_service),
):
    return service.despachar_envio(envio_id, payload)


@router.post(
    "/envios/{envio_id}/temperaturas",
    response_model=EnvioRead,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar la temperatura de salida antes de colocar el precinto",
)
def registrar_temperatura(
    envio_id: int,
    payload: RegistroTemperaturaCreate,
    service: EnvioService = Depends(get_service),
):
    return service.registrar_temperatura(envio_id, payload)


@router.post(
    "/envios/{envio_id}/incidencias",
    response_model=EnvioRead,
    status_code=status.HTTP_201_CREATED,
    summary="US-16: Registrar una incidencia durante el transporte",
)
def registrar_incidencia(
    envio_id: int,
    payload: IncidenciaTransporteCreate,
    service: EnvioService = Depends(get_service),
):
    return service.registrar_incidencia(envio_id, payload)


@router.get("/envios", response_model=list[EnvioRead], summary="Listar envíos y su trazabilidad")
def listar_envios(service: EnvioService = Depends(get_service)):
    return service.listar_envios()


@router.get("/envios/{envio_id}", response_model=EnvioRead, summary="Consultar el detalle de un envío")
def obtener_envio(envio_id: int, service: EnvioService = Depends(get_service)):
    return service.obtener_envio(envio_id)


@router.get("/envios/{envio_id}/remito", response_model=RemitoRead, summary="Consultar la copia histórica del remito")
def obtener_remito(envio_id: int, service: EnvioService = Depends(get_service)):
    return service.obtener_remito(envio_id)


@router.get(
    "/envios/{envio_id}/remito/impresion",
    response_class=HTMLResponse,
    summary="Abrir una versión imprimible del remito",
)
def imprimir_remito(envio_id: int, service: EnvioService = Depends(get_service)):
    return HTMLResponse(content=service.obtener_remito_html(envio_id))
