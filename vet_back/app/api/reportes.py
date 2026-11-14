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


class EnvioReporteRechazadasEmailEntrada(BaseModel):
    destinatario: str
    asunto: str | None = None
    incluir_pdf: bool = True
    incluir_excel: bool = True
    fecha_desde: str | None = None
    fecha_hasta: str | None = None
    causa: str | None = None
    causa_rechazo: str | None = None
    transportista: str | None = None
    estado_muestra: str | None = None
    estado: str | None = None


@router.get("/muestras-rechazadas", summary="Reporte 2: Muestras Rechazadas por Fallas en Transporte y Bioseguridad")
def obtener_reporte_muestras_rechazadas(
    fecha_desde: str | None = Query(None, description="Fecha inicio YYYY-MM-DD"),
    fecha_hasta: str | None = Query(None, description="Fecha fin YYYY-MM-DD"),
    causa: str | None = Query(None, description="Filtro por Causa Raíz de Rechazo"),
    causa_rechazo: str | None = Query(None, description="Alias para causa"),
    transportista: str | None = Query(None, description="Filtro por Transportista"),
    estado_muestra: str | None = Query(None, description="Filtro por Estado (Rechazada / Aceptada)"),
    estado: str | None = Query(None, description="Alias para estado_muestra"),
    service: ReportesService = Depends(get_service),
) -> dict[str, Any]:
    filtro_causa = causa or causa_rechazo
    filtro_estado = estado_muestra or estado
    return service.generar_reporte_muestras_rechazadas(
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        causa_filtro=filtro_causa,
        transportista_filtro=transportista,
        estado_filtro=filtro_estado,
    )


@router.get("/muestras-rechazadas/excel", summary="Descargar Reporte 2 en formato Excel (.xlsx)")
def descargar_reporte_muestras_rechazadas_excel(
    fecha_desde: str | None = Query(None),
    fecha_hasta: str | None = Query(None),
    causa: str | None = Query(None),
    causa_rechazo: str | None = Query(None),
    transportista: str | None = Query(None),
    estado_muestra: str | None = Query(None),
    estado: str | None = Query(None),
    service: ReportesService = Depends(get_service),
):
    filtro_causa = causa or causa_rechazo
    filtro_estado = estado_muestra or estado
    datos = service.generar_reporte_muestras_rechazadas(
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        causa_filtro=filtro_causa,
        transportista_filtro=transportista,
        estado_filtro=filtro_estado,
    )
    excel_bytes = service.exportar_excel_muestras_rechazadas(datos)
    nombre_archivo = "reporte_muestras_rechazadas_bioseguridad.xlsx"
    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{nombre_archivo}"'},
    )


@router.get("/muestras-rechazadas/pdf", summary="Descargar Reporte 2 en formato PDF oficial")
def descargar_reporte_muestras_rechazadas_pdf(
    fecha_desde: str | None = Query(None),
    fecha_hasta: str | None = Query(None),
    causa: str | None = Query(None),
    causa_rechazo: str | None = Query(None),
    transportista: str | None = Query(None),
    estado_muestra: str | None = Query(None),
    estado: str | None = Query(None),
    service: ReportesService = Depends(get_service),
):
    filtro_causa = causa or causa_rechazo
    filtro_estado = estado_muestra or estado
    datos = service.generar_reporte_muestras_rechazadas(
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        causa_filtro=filtro_causa,
        transportista_filtro=transportista,
        estado_filtro=filtro_estado,
    )
    pdf_bytes = service.exportar_pdf_muestras_rechazadas(datos)
    nombre_archivo = "reporte_muestras_rechazadas_bioseguridad.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{nombre_archivo}"'},
    )


@router.post("/muestras-rechazadas/enviar-email", summary="Enviar Reporte 2 por correo electrónico con adjuntos")
def enviar_reporte_muestras_rechazadas_email(
    payload: EnvioReporteRechazadasEmailEntrada,
    service: ReportesService = Depends(get_service),
) -> dict[str, Any]:
    filtro_causa = payload.causa or payload.causa_rechazo
    filtro_estado = payload.estado_muestra or payload.estado
    datos = service.generar_reporte_muestras_rechazadas(
        fecha_desde=payload.fecha_desde,
        fecha_hasta=payload.fecha_hasta,
        causa_filtro=filtro_causa,
        transportista_filtro=payload.transportista,
        estado_filtro=filtro_estado,
    )
    resultado = service.enviar_reporte_rechazadas_email(
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


class EnvioReporteRendimientoEmailEntrada(BaseModel):
    destinatario: str
    asunto: str | None = None
    incluir_pdf: bool = True
    incluir_excel: bool = True
    fecha_desde: str | None = None
    fecha_hasta: str | None = None
    veterinario: str | None = None
    veterinario_nombre: str | None = None
    especialidad: str | None = None
    estado_turno: str | None = None
    derivacion: str | None = None


@router.get("/rendimiento-clinico", summary="Reporte 3: Rendimiento Clínico y Tasa de Derivación Médica")
def obtener_reporte_rendimiento_clinico(
    fecha_desde: str | None = Query(None, description="Fecha inicio YYYY-MM-DD"),
    fecha_hasta: str | None = Query(None, description="Fecha fin YYYY-MM-DD"),
    veterinario: str | None = Query(None, description="Filtro por Médico Veterinario"),
    veterinario_nombre: str | None = Query(None, description="Alias para veterinario"),
    especialidad: str | None = Query(None, description="Filtro por Especialidad Médica"),
    estado_turno: str | None = Query(None, description="Filtro por Estado de Cita (Atendido / Ausente / Cancelado)"),
    derivacion: str | None = Query(None, description="Filtro por Derivación (Con Derivación / Sin Derivación)"),
    service: ReportesService = Depends(get_service),
) -> dict[str, Any]:
    filtro_vet = veterinario or veterinario_nombre
    return service.generar_reporte_rendimiento_clinico(
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        veterinario_filtro=filtro_vet,
        especialidad_filtro=especialidad,
        estado_turno_filtro=estado_turno,
        derivacion_filtro=derivacion,
    )


@router.get("/rendimiento-clinico/excel", summary="Descargar Reporte 3 en formato Excel (.xlsx)")
def descargar_reporte_rendimiento_clinico_excel(
    fecha_desde: str | None = Query(None),
    fecha_hasta: str | None = Query(None),
    veterinario: str | None = Query(None),
    veterinario_nombre: str | None = Query(None),
    especialidad: str | None = Query(None),
    estado_turno: str | None = Query(None),
    derivacion: str | None = Query(None),
    service: ReportesService = Depends(get_service),
):
    filtro_vet = veterinario or veterinario_nombre
    datos = service.generar_reporte_rendimiento_clinico(
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        veterinario_filtro=filtro_vet,
        especialidad_filtro=especialidad,
        estado_turno_filtro=estado_turno,
        derivacion_filtro=derivacion,
    )
    excel_bytes = service.exportar_excel_rendimiento_clinico(datos)
    nombre_archivo = "reporte_rendimiento_clinico_derivacion.xlsx"
    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{nombre_archivo}"'},
    )


@router.get("/rendimiento-clinico/pdf", summary="Descargar Reporte 3 en formato PDF oficial")
def descargar_reporte_rendimiento_clinico_pdf(
    fecha_desde: str | None = Query(None),
    fecha_hasta: str | None = Query(None),
    veterinario: str | None = Query(None),
    veterinario_nombre: str | None = Query(None),
    especialidad: str | None = Query(None),
    estado_turno: str | None = Query(None),
    derivacion: str | None = Query(None),
    service: ReportesService = Depends(get_service),
):
    filtro_vet = veterinario or veterinario_nombre
    datos = service.generar_reporte_rendimiento_clinico(
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        veterinario_filtro=filtro_vet,
        especialidad_filtro=especialidad,
        estado_turno_filtro=estado_turno,
        derivacion_filtro=derivacion,
    )
    pdf_bytes = service.exportar_pdf_rendimiento_clinico(datos)
    nombre_archivo = "reporte_rendimiento_clinico_derivacion.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{nombre_archivo}"'},
    )


@router.post("/rendimiento-clinico/enviar-email", summary="Enviar Reporte 3 por correo electrónico con adjuntos")
def enviar_reporte_rendimiento_clinico_email(
    payload: EnvioReporteRendimientoEmailEntrada,
    service: ReportesService = Depends(get_service),
) -> dict[str, Any]:
    filtro_vet = payload.veterinario or payload.veterinario_nombre
    datos = service.generar_reporte_rendimiento_clinico(
        fecha_desde=payload.fecha_desde,
        fecha_hasta=payload.fecha_hasta,
        veterinario_filtro=filtro_vet,
        especialidad_filtro=payload.especialidad,
        estado_turno_filtro=payload.estado_turno,
        derivacion_filtro=payload.derivacion,
    )
    resultado = service.enviar_reporte_rendimiento_email(
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


