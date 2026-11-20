from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.orden_analisis import Muestra
from app.models.recepcion import ResultadoAnalisis
from app.services.reportes.base import fecha_hora_argentina_str, exportar_reporte_excel, exportar_reporte_pdf, enviar_reporte_email as enviar_reporte_email_adjuntos

class ServicioTiemposSla:
    def __init__(self, db: Session) -> None:
        self.db = db

    def generar_reporte_tiempos_sla(
        self,
        fecha_desde: str | None = None,
        fecha_hasta: str | None = None,
        tipo_analisis_filtro: str | None = None,
        transportista_filtro: str | None = None,
        prioridad_filtro: str | None = None,
    ) -> dict[str, Any]:
        """Reporte de extracción y resultados, basado en muestras y resultados persistidos."""
        detalles_todos = self._recopilar_detalles_muestras()

        # Opciones completas para los filtros disponibles basadas en el universo total
        todos_tipos = sorted(list(set(d["tipo_analisis"] for d in detalles_todos if d.get("tipo_analisis"))))
        todos_transp: list[str] = []

        detalles_muestras = detalles_todos
        if fecha_desde:
            detalles_muestras = [d for d in detalles_muestras if d["fecha_extraccion"][:10] >= fecha_desde[:10]]
        if fecha_hasta:
            detalles_muestras = [d for d in detalles_muestras if d["fecha_extraccion"][:10] <= fecha_hasta[:10]]
        if tipo_analisis_filtro and tipo_analisis_filtro != "Todos":
            detalles_muestras = [
                d for d in detalles_muestras
                if (d.get("tipo_analisis") or "").strip().lower() == tipo_analisis_filtro.strip().lower()
            ]
        if transportista_filtro and transportista_filtro != "Todos":
            detalles_muestras = [
                d for d in detalles_muestras
                if (d.get("transportista") or "").strip().lower() == transportista_filtro.strip().lower()
            ]
        if prioridad_filtro and prioridad_filtro != "Todas":
            detalles_muestras = [
                d for d in detalles_muestras
                if (d.get("prioridad") or "").strip().lower() == prioridad_filtro.strip().lower()
            ]

        total_muestras = len(detalles_muestras)
        total_resultados = sum(d["tiene_resultado"] for d in detalles_muestras)
        por_tipo: dict[str, int] = {}
        for d in detalles_muestras:
            por_tipo[d["tipo_muestra"]] = por_tipo.get(d["tipo_muestra"], 0) + 1
        sla_por_tipo_analisis = [
            {"tipo_muestra": tipo, "cantidad": cantidad}
            for tipo, cantidad in sorted(por_tipo.items(), key=lambda par: (-par[1], par[0]))
        ]
        return {
            "fecha_generacion": fecha_hora_argentina_str(),
            "kpis": {
                "total_muestras_extraidas": total_muestras,
                "muestras_con_resultado": total_resultados,
                "muestras_sin_resultado": total_muestras - total_resultados,
                "porcentaje_con_resultado": round(total_resultados / total_muestras * 100, 1) if total_muestras else None,
            },
            "distribucion_tipo_muestra": sla_por_tipo_analisis,
            "comparacion_muestras": [
                {"estado": "Extraídas", "cantidad": total_muestras},
                {"estado": "Con resultado", "cantidad": total_resultados},
                {"estado": "Sin resultado", "cantidad": total_muestras-total_resultados},
            ],
            "filtros_disponibles": {
                "tipos_analisis": todos_tipos,
            },
        }

    def _recopilar_detalles_muestras(self) -> list[dict[str, Any]]:
        from app.services.recepcion import normalizar_fecha_utc

        resultados = self.db.scalars(select(ResultadoAnalisis)).all()
        resultados_por_muestra: dict[str, list[ResultadoAnalisis]] = {}
        for resultado in resultados:
            if resultado.muestra_id and resultado.estado == "recibido":
                resultados_por_muestra.setdefault(str(resultado.muestra_id), []).append(resultado)
        resultados_por_detalle_sin_muestra: dict[str, list[ResultadoAnalisis]] = {}
        for resultado in resultados:
            if not resultado.muestra_id and resultado.estado == "recibido":
                resultados_por_detalle_sin_muestra.setdefault(str(resultado.detalle_orden_id), []).append(resultado)
        muestras_por_detalle: dict[str, int] = {}
        for muestra in self.db.scalars(select(Muestra)).all():
            for asociacion in muestra.asociaciones_detalles:
                detalle_id = str(asociacion.detalle_id)
                muestras_por_detalle[detalle_id] = muestras_por_detalle.get(detalle_id, 0) + 1
        registros = []
        for muestra in self.db.scalars(select(Muestra)).all():
            orden = muestra.orden
            consulta = orden.consulta if orden else None
            paciente = consulta.pet if consulta else None
            tipo_muestra = muestra.tipo_muestra.nombre if muestra.tipo_muestra else "Sin tipo registrado"
            fecha_extraccion = muestra.fecha_extraccion
            resultados_explicitos = any(
                fecha_extraccion is not None
                and normalizar_fecha_utc(resultado.fecha_recepcion) >= normalizar_fecha_utc(fecha_extraccion)
                for resultado in resultados_por_muestra.get(str(muestra.id), [])
            )
            resultado_legacy_sin_muestra = any(
                muestras_por_detalle.get(str(asociacion.detalle_id)) == 1
                and fecha_extraccion is not None
                and any(
                    normalizar_fecha_utc(resultado.fecha_recepcion) >= normalizar_fecha_utc(fecha_extraccion)
                    for resultado in resultados_por_detalle_sin_muestra.get(str(asociacion.detalle_id), [])
                )
                for asociacion in muestra.asociaciones_detalles
            )
            tiene_resultado = resultados_explicitos or resultado_legacy_sin_muestra
            registros.append({
                "muestra_codigo": muestra.codigo_etiqueta,
                "fecha_extraccion": muestra.fecha_extraccion.strftime("%Y-%m-%d %H:%M") if muestra.fecha_extraccion else "Sin fecha",
                "tipo_muestra": tipo_muestra,
                "tipo_analisis": tipo_muestra,
                "estado_muestra": muestra.estado,
                "paciente_nombre": paciente.name if paciente else "Sin dato",
                "tiene_resultado": tiene_resultado,
                "estado_analisis": "Con resultado" if tiene_resultado else "Pendiente de resultado",
            })
        return registros

    def exportar_excel(self, datos: dict[str, Any]) -> bytes:
        return exportar_reporte_excel("Estadísticas de muestras y análisis", datos, [("Distribución por tipo de muestra", "distribucion_tipo_muestra"), ("Muestras extraídas y con resultado", "comparacion_muestras")])


    def exportar_pdf(self, datos: dict[str, Any]) -> bytes:
        return exportar_reporte_pdf("Estadísticas de muestras y análisis", datos, [("Distribución por tipo de muestra", "distribucion_tipo_muestra"), ("Muestras extraídas y con resultado", "comparacion_muestras")])


    def enviar_reporte_email(
        self,
        destinatario: str,
        asunto: str | None = None,
        incluir_pdf: bool = True,
        incluir_excel: bool = True,
        datos: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        datos = datos or self.generar_reporte_tiempos_sla()
        return enviar_reporte_email_adjuntos(destinatario, asunto, incluir_pdf, incluir_excel, datos, "reporte_muestras_y_analisis", self.exportar_pdf, self.exportar_excel)

