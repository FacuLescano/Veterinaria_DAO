from typing import Any
from sqlalchemy.orm import Session

from app.services.reportes.base import RUTA_LOGO
from app.services.reportes.servicio_tiempos_sla import ServicioTiemposSla, MATRIZ_SLA
from app.services.reportes.servicio_muestras_rechazadas import ServicioMuestrasRechazadas
from app.services.reportes.servicio_rendimiento_clinico import ServicioRendimientoClinico
from app.services.reportes.servicio_eficacia_diagnostica import ServicioEficaciaDiagnostica

__all__ = ["ReportesService", "MATRIZ_SLA", "RUTA_LOGO"]


class ReportesService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self._servicio_tiempos = ServicioTiemposSla(db)
        self._servicio_rechazadas = ServicioMuestrasRechazadas(db)
        self._servicio_rendimiento = ServicioRendimientoClinico(db)
        self._servicio_eficacia = ServicioEficaciaDiagnostica(db)

    def obtener_sla_objetivo(self, tipo_analisis: str, prioridad: str) -> float:
        return self._servicio_tiempos.obtener_sla_objetivo(tipo_analisis, prioridad)

    def generar_reporte_tiempos_sla(
        self,
        fecha_desde: str | None = None,
        fecha_hasta: str | None = None,
        tipo_analisis_filtro: str | None = None,
        transportista_filtro: str | None = None,
        prioridad_filtro: str | None = None,
    ) -> dict[str, Any]:
        return self._servicio_tiempos.generar_reporte_tiempos_sla(
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            tipo_analisis_filtro=tipo_analisis_filtro,
            transportista_filtro=transportista_filtro,
            prioridad_filtro=prioridad_filtro,
        )

    def exportar_excel(self, datos: dict[str, Any]) -> bytes:
        return self._servicio_tiempos.exportar_excel(datos)

    def exportar_pdf(self, datos: dict[str, Any]) -> bytes:
        return self._servicio_tiempos.exportar_pdf(datos)

    def enviar_reporte_email(
        self,
        destinatario: str,
        asunto: str | None = None,
        incluir_pdf: bool = True,
        incluir_excel: bool = True,
        datos: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self._servicio_tiempos.enviar_reporte_email(
            destinatario=destinatario,
            asunto=asunto,
            incluir_pdf=incluir_pdf,
            incluir_excel=incluir_excel,
            datos=datos,
        )

    def generar_reporte_muestras_rechazadas(
        self,
        fecha_desde: str | None = None,
        fecha_hasta: str | None = None,
        causa_filtro: str | None = None,
        transportista_filtro: str | None = None,
        estado_filtro: str | None = None,
    ) -> dict[str, Any]:
        return self._servicio_rechazadas.generar_reporte_muestras_rechazadas(
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            causa_filtro=causa_filtro,
            transportista_filtro=transportista_filtro,
            estado_filtro=estado_filtro,
        )

    def exportar_excel_muestras_rechazadas(self, datos: dict[str, Any]) -> bytes:
        return self._servicio_rechazadas.exportar_excel_muestras_rechazadas(datos)

    def exportar_pdf_muestras_rechazadas(self, datos: dict[str, Any]) -> bytes:
        return self._servicio_rechazadas.exportar_pdf_muestras_rechazadas(datos)

    def enviar_reporte_rechazadas_email(
        self,
        destinatario: str,
        asunto: str | None = None,
        incluir_pdf: bool = True,
        incluir_excel: bool = True,
        datos: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self._servicio_rechazadas.enviar_reporte_rechazadas_email(
            destinatario=destinatario,
            asunto=asunto,
            incluir_pdf=incluir_pdf,
            incluir_excel=incluir_excel,
            datos=datos,
        )

    def generar_reporte_rendimiento_clinico(
        self,
        fecha_desde: str | None = None,
        fecha_hasta: str | None = None,
        veterinario_filtro: str | None = None,
        especialidad_filtro: str | None = None,
        estado_turno_filtro: str | None = None,
        derivacion_filtro: str | None = None,
    ) -> dict[str, Any]:
        return self._servicio_rendimiento.generar_reporte_rendimiento_clinico(
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            veterinario_filtro=veterinario_filtro,
            especialidad_filtro=especialidad_filtro,
            estado_turno_filtro=estado_turno_filtro,
            derivacion_filtro=derivacion_filtro,
        )

    def exportar_excel_rendimiento_clinico(self, datos: dict[str, Any]) -> bytes:
        return self._servicio_rendimiento.exportar_excel_rendimiento_clinico(datos)

    def exportar_pdf_rendimiento_clinico(self, datos: dict[str, Any]) -> bytes:
        return self._servicio_rendimiento.exportar_pdf_rendimiento_clinico(datos)

    def enviar_reporte_rendimiento_email(
        self,
        destinatario: str,
        asunto: str | None = None,
        incluir_pdf: bool = True,
        incluir_excel: bool = True,
        datos: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self._servicio_rendimiento.enviar_reporte_rendimiento_email(
            destinatario=destinatario,
            asunto=asunto,
            incluir_pdf=incluir_pdf,
            incluir_excel=incluir_excel,
            datos=datos,
        )

    # ==========================================
    # Métodos para Reporte 4: Eficacia Diagnóstica & Hallazgos Críticos
    # ==========================================

    def generar_reporte_eficacia_diagnostica(
        self,
        fecha_desde: str | None = None,
        fecha_hasta: str | None = None,
        especie_filtro: str | None = None,
        grupo_etario_filtro: str | None = None,
        estado_diagnostico_filtro: str | None = None,
        tipo_analisis_filtro: str | None = None,
    ) -> dict[str, Any]:
        return self._servicio_eficacia.generar_reporte_eficacia_diagnostica(
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            especie_filtro=especie_filtro,
            grupo_etario_filtro=grupo_etario_filtro,
            estado_diagnostico_filtro=estado_diagnostico_filtro,
            tipo_analisis_filtro=tipo_analisis_filtro,
        )

    def exportar_excel_eficacia_diagnostica(self, datos: dict[str, Any]) -> bytes:
        return self._servicio_eficacia.exportar_excel_eficacia_diagnostica(datos)

    def exportar_pdf_eficacia_diagnostica(self, datos: dict[str, Any]) -> bytes:
        return self._servicio_eficacia.exportar_pdf_eficacia_diagnostica(datos)

    def enviar_reporte_eficacia_email(
        self,
        destinatario: str,
        asunto: str | None = None,
        incluir_pdf: bool = True,
        incluir_excel: bool = True,
        datos: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self._servicio_eficacia.enviar_reporte_eficacia_email(
            destinatario=destinatario,
            asunto=asunto,
            incluir_pdf=incluir_pdf,
            incluir_excel=incluir_excel,
            datos=datos,
        )
