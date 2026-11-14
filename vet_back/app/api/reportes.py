from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.reportes_service import ReportesService

router = APIRouter(prefix="/api/v1/reportes", tags=["Módulo de Reportes & Analítica"])


def get_service(db: Session = Depends(get_db)) -> ReportesService:
    return ReportesService(db)


class EnvioReporteEmailEntrada(BaseModel):
    destinatario: str
    asunto: str | None = None
    incluir_pdf: bool = True
    incluir_excel: bool = True
    fecha_desde: str | None = None
    fecha_hasta: str | None = None
    tipo_analisis: str | None = None
    transportista: str | None = None
    prioridad: str | None = None


@router.get("/tiempos-sla", summary="Reporte 1: Tiempo Promedio de Tránsito y Cumplimiento de SLA")
def obtener_reporte_tiempos_sla(
    fecha_desde: str | None = Query(None, description="Fecha inicio YYYY-MM-DD"),
    fecha_hasta: str | None = Query(None, description="Fecha fin YYYY-MM-DD"),
    tipo_analisis: str | None = Query(None, description="Filtro por Tipo de Análisis"),
    transportista: str | None = Query(None, description="Filtro por Transportista"),
    prioridad: str | None = Query(None, description="Filtro por Prioridad (Normal / Urgente)"),
    service: ReportesService = Depends(get_service),
) -> dict[str, Any]:
    return service.generar_reporte_tiempos_sla(
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        tipo_analisis_filtro=tipo_analisis,
        transportista_filtro=transportista,
        prioridad_filtro=prioridad,
    )


@router.get("/tiempos-sla/excel", summary="Descargar Reporte 1 en formato Excel (.xlsx)")
def descargar_reporte_tiempos_sla_excel(
    fecha_desde: str | None = Query(None),
    fecha_hasta: str | None = Query(None),
    tipo_analisis: str | None = Query(None),
    transportista: str | None = Query(None),
    prioridad: str | None = Query(None),
    service: ReportesService = Depends(get_service),
):
    datos = service.generar_reporte_tiempos_sla(
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        tipo_analisis_filtro=tipo_analisis,
        transportista_filtro=transportista,
        prioridad_filtro=prioridad,
    )
    excel_bytes = service.exportar_excel(datos)
    nombre_archivo = "reporte_tiempos_transito_sla.xlsx"
    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{nombre_archivo}"'},
    )


@router.get("/tiempos-sla/pdf", summary="Descargar Reporte 1 en formato PDF oficial")
def descargar_reporte_tiempos_sla_pdf(
    fecha_desde: str | None = Query(None),
    fecha_hasta: str | None = Query(None),
    tipo_analisis: str | None = Query(None),
    transportista: str | None = Query(None),
    prioridad: str | None = Query(None),
    service: ReportesService = Depends(get_service),
):
    datos = service.generar_reporte_tiempos_sla(
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        tipo_analisis_filtro=tipo_analisis,
        transportista_filtro=transportista,
        prioridad_filtro=prioridad,
    )
    pdf_bytes = service.exportar_pdf(datos)
    nombre_archivo = "reporte_tiempos_transito_sla.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{nombre_archivo}"'},
    )


@router.post("/tiempos-sla/enviar-email", summary="Enviar Reporte 1 por correo electrónico con adjuntos")
def enviar_reporte_tiempos_sla_email(
    payload: EnvioReporteEmailEntrada,
    service: ReportesService = Depends(get_service),
) -> dict[str, Any]:
    datos = service.generar_reporte_tiempos_sla(
        fecha_desde=payload.fecha_desde,
        fecha_hasta=payload.fecha_hasta,
        tipo_analisis_filtro=payload.tipo_analisis,
        transportista_filtro=payload.transportista,
        prioridad_filtro=payload.prioridad,
    )
    resultado = service.enviar_reporte_email(
        destinatario=payload.destinatario,
        asunto=payload.asunto,
        incluir_pdf=payload.incluir_pdf,
        incluir_excel=payload.incluir_excel,
        datos=datos,
    )
    if not resultado["exito"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=resultado["mensaje"],
        )
    return resultado

