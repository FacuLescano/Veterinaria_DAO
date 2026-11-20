"""Seguimiento de resultados recibidos y análisis pendientes."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.orden_analisis import DetalleOrdenAnalisis, Muestra
from app.models.recepcion import RecepcionEnvio, ResultadoAnalisis
from app.services.recepcion import normalizar_fecha_utc, recepcion_pertenece_al_envio_actual
from app.services.reportes.base import fecha_hora_argentina_str, exportar_reporte_excel, exportar_reporte_pdf, enviar_reporte_email as enviar_reporte_email_adjuntos


class ServicioEficaciaDiagnostica:
    """Servicio con la lógica de negocio, exportaciones y métricas para el Reporte 4."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def generar_reporte_eficacia_diagnostica(
        self,
        fecha_desde: str | None = None,
        fecha_hasta: str | None = None,
        especie_filtro: str | None = None,
        grupo_etario_filtro: str | None = None,
        estado_diagnostico_filtro: str | None = None,
        tipo_analisis_filtro: str | None = None,
    ) -> dict[str, Any]:
        """Resume resultados recibidos y análisis pendientes usando registros del dominio."""
        detalles = self.db.scalars(select(DetalleOrdenAnalisis)).all()
        todos_tipos = sorted({d.tipo_analisis.nombre for d in detalles if d.tipo_analisis})
        detalles_periodo = []
        for detalle in detalles:
            orden = detalle.orden
            fecha_orden = orden.created_at if orden else None
            if (fecha_desde or fecha_hasta) and not fecha_orden:
                continue
            if fecha_orden and fecha_desde and fecha_orden.strftime("%Y-%m-%d") < fecha_desde[:10]:
                continue
            if fecha_orden and fecha_hasta and fecha_orden.strftime("%Y-%m-%d") > fecha_hasta[:10]:
                continue
            nombre_tipo = detalle.tipo_analisis.nombre if detalle.tipo_analisis else "Sin tipo"
            if tipo_analisis_filtro and tipo_analisis_filtro != "Todos" and nombre_tipo.casefold() != tipo_analisis_filtro.casefold():
                continue
            detalles_periodo.append(detalle)

        ids_detalle_periodo = {str(d.id) for d in detalles_periodo}
        detalles_por_id = {str(d.id): d for d in detalles_periodo}
        resultados = self.db.scalars(
            select(ResultadoAnalisis).where(ResultadoAnalisis.estado == "recibido")
        ).all()
        resultados_vigentes = [
            resultado for resultado in resultados
            if str(resultado.detalle_orden_id) in ids_detalle_periodo
            and detalles_por_id[str(resultado.detalle_orden_id)].orden
            and detalles_por_id[str(resultado.detalle_orden_id)].orden.created_at
            and normalizar_fecha_utc(resultado.fecha_recepcion)
            >= normalizar_fecha_utc(detalles_por_id[str(resultado.detalle_orden_id)].orden.created_at)
        ]
        resultados_del_periodo = [
            resultado for resultado in resultados_vigentes
            if (not fecha_desde or resultado.fecha_recepcion.strftime("%Y-%m-%d") >= fecha_desde[:10])
            and (not fecha_hasta or resultado.fecha_recepcion.strftime("%Y-%m-%d") <= fecha_hasta[:10])
        ]
        ids_con_resultado = {str(r.detalle_orden_id) for r in resultados_vigentes}
        recibidos = len(ids_con_resultado)
        pendientes = len(detalles_periodo) - recibidos
        porcentaje = round(recibidos / len(detalles_periodo) * 100, 1) if detalles_periodo else None

        recepciones = self.db.scalars(select(RecepcionEnvio)).all()
        recepciones_por_envio: dict[str, list[RecepcionEnvio]] = {}
        for recepcion in recepciones:
            recepciones_por_envio.setdefault(str(recepcion.envio_id), []).append(recepcion)
        duraciones = []
        for resultado in resultados_del_periodo:
            if not resultado.muestra_id:
                continue
            try:
                muestra = self.db.get(Muestra, int(resultado.muestra_id))
            except (TypeError, ValueError):
                muestra = None
            envio = muestra.envio if muestra else None
            recepcion = None
            if envio:
                recepcion = max(
                    (
                        registro for registro in recepciones_por_envio.get(str(envio.id), [])
                        if recepcion_pertenece_al_envio_actual(registro, envio)
                    ),
                    key=lambda registro: normalizar_fecha_utc(registro.fecha_recepcion),
                    default=None,
                )
            if not (muestra and recepcion and str(muestra.id) in {str(x) for x in recepcion.muestras_recibidas or []}):
                continue
            horas = (normalizar_fecha_utc(resultado.fecha_recepcion) - normalizar_fecha_utc(recepcion.fecha_recepcion)).total_seconds() / 3600
            if horas >= 0:
                duraciones.append(horas)
        promedio = round(sum(duraciones) / len(duraciones), 1) if duraciones else None
        conteo_fecha = self._conteo_por_fecha(resultados_del_periodo)
        antiguedad = self._antiguedad_pendientes(detalles_periodo, ids_con_resultado)
        return {
            "fecha_generacion": fecha_hora_argentina_str(),
            "kpis": {
                "resultados_recibidos": recibidos,
                "analisis_pendientes": pendientes,
                "porcentaje_con_resultado": porcentaje,
                "tiempo_promedio_respuesta_horas": promedio,
                "total_analisis_solicitados": len(detalles_periodo),
            },
            "evolucion_resultados": [
                {"fecha": fecha, "cantidad": cantidad} for fecha, cantidad in sorted(conteo_fecha.items())
            ],
            "estado_resultados": [
                {"estado": "Con resultado", "cantidad": recibidos},
                {"estado": "Pendiente", "cantidad": pendientes},
            ],
            "tiempos_respuesta": [{"período": "Promedio", "tiempo_promedio_horas": promedio}] if promedio is not None else [],
            "antiguedad_pendientes_dias": antiguedad,
            "filtros_disponibles": {"tipos_analisis": ["Todos"] + todos_tipos},
        }
    @staticmethod
    def _conteo_por_fecha(resultados: list[ResultadoAnalisis]) -> dict[str, int]:
        conteo: dict[str, int] = {}
        for resultado in resultados:
            fecha = resultado.fecha_recepcion.strftime("%Y-%m-%d")
            conteo[fecha] = conteo.get(fecha, 0) + 1
        return conteo

    @staticmethod
    def _antiguedad_pendientes(
        detalles: list[DetalleOrdenAnalisis], detalle_ids_con_resultado: set[str]
    ) -> list[dict[str, Any]]:
        ahora = datetime.now(timezone.utc).replace(tzinfo=None)
        pendientes = []
        for detalle in detalles:
            if str(detalle.id) in detalle_ids_con_resultado:
                continue
            orden = detalle.orden
            fecha = orden.created_at.replace(tzinfo=None) if orden and orden.created_at else None
            if fecha:
                pendientes.append({
                    "analisis": detalle.tipo_analisis.nombre if detalle.tipo_analisis else "Análisis",
                    "antiguedad_dias": max(0, (ahora - fecha).days),
                })
        return sorted(pendientes, key=lambda item: item["antiguedad_dias"], reverse=True)


    def exportar_excel_eficacia_diagnostica(self, datos: dict[str, Any]) -> bytes:
        return exportar_reporte_excel("Seguimiento de resultados de laboratorio", datos, [("Estado de resultados", "estado_resultados"), ("Tiempo de respuesta", "tiempos_respuesta"), ("Evolución de resultados", "evolucion_resultados"), ("Antigüedad de análisis pendientes", "antiguedad_pendientes_dias")])


    def exportar_pdf_eficacia_diagnostica(self, datos: dict[str, Any]) -> bytes:
        return exportar_reporte_pdf("Seguimiento de resultados de laboratorio", datos, [("Estado de resultados", "estado_resultados"), ("Tiempo de respuesta", "tiempos_respuesta"), ("Evolución de resultados", "evolucion_resultados"), ("Antigüedad de análisis pendientes", "antiguedad_pendientes_dias")])


    def enviar_reporte_eficacia_email(
        self,
        destinatario: str,
        asunto: str | None = None,
        incluir_pdf: bool = True,
        incluir_excel: bool = True,
        datos: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        datos = datos or self.generar_reporte_eficacia_diagnostica()
        return enviar_reporte_email_adjuntos(destinatario, asunto, incluir_pdf, incluir_excel, datos, "reporte_seguimiento_resultados", self.exportar_pdf_eficacia_diagnostica, self.exportar_excel_eficacia_diagnostica)
