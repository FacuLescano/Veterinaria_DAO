from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.orden_analisis import Muestra
from app.services.reportes.base import fecha_hora_argentina_str, exportar_reporte_excel, exportar_reporte_pdf, enviar_reporte_email as enviar_reporte_email_adjuntos



class ServicioMuestrasRechazadas:
    def __init__(self, db: Session) -> None:
        self.db = db

    def generar_reporte_muestras_rechazadas(
        self,
        fecha_desde: str | None = None,
        fecha_hasta: str | None = None,
        transportista_filtro: str | None = None,
        estado_filtro: str | None = None,
    ) -> dict[str, Any]:
        """Resume estados de recepción y tiempos efectivos de ingreso al laboratorio."""
        detalles = self._recopilar_detalles_rechazadas()
        transportistas = sorted({d["transportista"] for d in detalles})
        if fecha_desde:
            detalles = [d for d in detalles if d["fecha_extraccion"][:10] >= fecha_desde[:10]]
        if fecha_hasta:
            detalles = [d for d in detalles if d["fecha_extraccion"][:10] <= fecha_hasta[:10]]
        if transportista_filtro and transportista_filtro != "Todos":
            detalles = [d for d in detalles if d["transportista"].casefold() == transportista_filtro.casefold()]
        if estado_filtro and estado_filtro != "Todos":
            detalles = [d for d in detalles if d["estado_muestra"].casefold() == estado_filtro.casefold()]

        estados = {estado: sum(d["estado_muestra"] == estado for d in detalles) for estado in ("Pendiente", "Aceptada", "Rechazada")}
        decididas = estados["Aceptada"] + estados["Rechazada"]
        total = len(detalles)
        tiempos_por_fecha: dict[str, list[float]] = {}
        for detalle in detalles:
            horas = detalle["tiempo_recepcion_horas"]
            fecha = detalle["fecha_recepcion_lab"][:10] if detalle["fecha_recepcion_lab"] else ""
            if horas is not None and fecha:
                tiempos_por_fecha.setdefault(fecha, []).append(horas)
        tiempos = [horas for grupo in tiempos_por_fecha.values() for horas in grupo]
        evolucion_tiempos = [
            {"fecha": fecha, "tiempo_promedio_horas": round(sum(valores) / len(valores), 1), "tiempo_minimo_horas": round(min(valores), 1), "tiempo_maximo_horas": round(max(valores), 1)}
            for fecha, valores in sorted(tiempos_por_fecha.items())
        ]
        return {
            "fecha_generacion": fecha_hora_argentina_str(),
            "kpis": {
                "muestras_aceptadas": estados["Aceptada"],
                "muestras_rechazadas": estados["Rechazada"],
                "muestras_pendientes": estados["Pendiente"],
                "porcentaje_aceptadas": round(estados["Aceptada"] / decididas * 100, 1) if decididas else None,
                "porcentaje_rechazadas": round(estados["Rechazada"] / decididas * 100, 1) if decididas else None,
                "tiempo_promedio_recepcion_horas": round(sum(tiempos) / len(tiempos), 1) if tiempos else None,
            },
            "distribucion_estados_recepcion": [
                {"estado": estado, "cantidad": cantidad, "porcentaje": round(cantidad / total * 100, 1) if total else None}
                for estado, cantidad in estados.items()
            ],
            "tiempos_recepcion": evolucion_tiempos,
            "filtros_disponibles": {"transportistas": ["Todos"] + transportistas, "estados": ["Todos", "Pendiente", "Aceptada", "Rechazada"]},
        }

    def _recopilar_detalles_rechazadas(self) -> list[dict[str, Any]]:
        from app.models.recepcion import RecepcionEnvio
        from app.services.recepcion import (
            normalizar_fecha_utc,
            recepcion_pertenece_al_envio_actual,
            verificacion_actual_del_envio,
        )

        recepciones = self.db.scalars(select(RecepcionEnvio)).all()
        recepciones_por_envio: dict[str, list[RecepcionEnvio]] = {}
        for recepcion in recepciones:
            recepciones_por_envio.setdefault(str(recepcion.envio_id), []).append(recepcion)
        registros = []
        for muestra in self.db.scalars(select(Muestra)).all():
            envio = muestra.envio
            verif = verificacion_actual_del_envio(self.db, envio) if envio else None
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
            codigo_invalido = bool(verif and verif.codigo_esperado is not None and verif.codigo_observado != verif.codigo_esperado)
            rechazada = muestra.estado == "rechazada" or bool(verif and (verif.estado.strip().lower() != "integro" or codigo_invalido))
            recibida = bool(recepcion and str(muestra.id) in {str(x) for x in (recepcion.muestras_recibidas or [])})
            aceptada = bool(
                not rechazada
                and recibida
                and verif
                and verif.estado.strip().lower() == "integro"
                and not codigo_invalido
            )
            fecha_recepcion = recepcion.fecha_recepcion if recibida else None
            horas = None
            if fecha_recepcion and muestra.fecha_extraccion:
                delta = (fecha_recepcion - muestra.fecha_extraccion).total_seconds() / 3600
                horas = round(delta, 1) if delta >= 0 else None
            registros.append({
                "muestra_codigo": muestra.codigo_etiqueta,
                "fecha_extraccion": muestra.fecha_extraccion.strftime("%Y-%m-%d %H:%M") if muestra.fecha_extraccion else "",
                "fecha_recepcion_lab": fecha_recepcion.strftime("%Y-%m-%d %H:%M") if fecha_recepcion else "",
                "tiempo_recepcion_horas": horas,
                "estado_muestra": "Rechazada" if rechazada else "Aceptada" if aceptada else "Pendiente",
                "transportista": envio.transportista or "Sin dato" if envio else "Sin envío",
            })
        return registros

    def exportar_excel_muestras_rechazadas(self, datos: dict[str, Any]) -> bytes:
        return exportar_reporte_excel("Recepción de muestras en laboratorio", datos, [("Recepción por estado", "distribucion_estados_recepcion"), ("Tiempo de recepción", "tiempos_recepcion")])


    def exportar_pdf_muestras_rechazadas(self, datos: dict[str, Any]) -> bytes:
        return exportar_reporte_pdf("Recepción de muestras en laboratorio", datos, [("Recepción por estado", "distribucion_estados_recepcion"), ("Tiempo de recepción", "tiempos_recepcion")])


    def enviar_reporte_rechazadas_email(
        self,
        destinatario: str,
        asunto: str | None = None,
        incluir_pdf: bool = True,
        incluir_excel: bool = True,
        datos: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        datos = datos or self.generar_reporte_muestras_rechazadas()
        return enviar_reporte_email_adjuntos(destinatario, asunto, incluir_pdf, incluir_excel, datos, "reporte_recepcion_muestras", self.exportar_pdf_muestras_rechazadas, self.exportar_excel_muestras_rechazadas)

