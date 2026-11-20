import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.orden_analisis import OrdenAnalisis
from app.models.paciente import Consulta, Turno
from app.services.reportes.base import fecha_hora_argentina_str, exportar_reporte_excel, exportar_reporte_pdf, enviar_reporte_email as enviar_reporte_email_adjuntos

logger = logging.getLogger(__name__)


class ServicioRendimientoClinico:

    def __init__(self, db: Session) -> None:
        self.db = db

    def generar_reporte_rendimiento_clinico(
        self,
        fecha_desde: str | None = None,
        fecha_hasta: str | None = None,
        veterinario_filtro: str | None = None,
        especialidad_filtro: str | None = None,
        estado_turno_filtro: str | None = None,
        derivacion_filtro: str | None = None,
    ) -> dict[str, Any]:
        detalles_todos = self._recopilar_detalles_clinicos()
        vets_disponibles = sorted({d["veterinario_nombre"] for d in detalles_todos if d.get("veterinario_nombre")})
        especialidades = sorted({d["especialidad"] for d in detalles_todos if d.get("especialidad")})
        detalles = detalles_todos
        if fecha_desde:
            detalles = [d for d in detalles if d["fecha_hora"][:10] >= fecha_desde[:10]]
        if fecha_hasta:
            detalles = [d for d in detalles if d["fecha_hora"][:10] <= fecha_hasta[:10]]
        if veterinario_filtro and veterinario_filtro != "Todos":
            filtro = veterinario_filtro.strip().casefold()
            detalles = [d for d in detalles if filtro in (d.get("veterinario_nombre") or "").casefold()]
        if especialidad_filtro and especialidad_filtro != "Todas":
            detalles = [d for d in detalles if (d.get("especialidad") or "").casefold() == especialidad_filtro.casefold()]
        if estado_turno_filtro and estado_turno_filtro != "Todos":
            detalles = [d for d in detalles if (d.get("estado_turno") or "").casefold() == estado_turno_filtro.casefold()]
        if derivacion_filtro and derivacion_filtro != "Todos":
            requiere_orden = derivacion_filtro == "Con Derivación"
            detalles = [d for d in detalles if d.get("derivo_laboratorio") is requiere_orden]

        turnos = [d for d in detalles if d.get("turno_id") != "Sin turno"]
        consultas = [d for d in detalles if d.get("consulta_realizada")]
        atendidos = sum(d["estado_turno"] == "Atendido" for d in turnos)
        ausentes = sum(d["estado_turno"] == "Ausente" for d in turnos)
        cancelados = sum(d["estado_turno"] == "Cancelado" for d in turnos)
        con_orden = sum(bool(d["derivo_laboratorio"]) for d in consultas)
        porcentaje_orden = round(con_orden / len(consultas) * 100, 1) if consultas else None

        consultas_por_veterinario: dict[str, int] = {}
        for consulta in consultas:
            nombre = consulta["veterinario_nombre"]
            consultas_por_veterinario[nombre] = consultas_por_veterinario.get(nombre, 0) + 1
        actividad_veterinarios = [
            {"veterinario_nombre": nombre, "consultas_realizadas": cantidad}
            for nombre, cantidad in sorted(consultas_por_veterinario.items(), key=lambda par: (-par[1], par[0]))
        ]
        distribucion = [
            {"estado": estado, "cantidad": cantidad, "porcentaje": round(cantidad / len(turnos) * 100, 1) if turnos else None}
            for estado, cantidad in (("Atendido", atendidos), ("Cancelado", cancelados), ("Ausente", ausentes))
        ]
        return {
            "fecha_generacion": fecha_hora_argentina_str(),
            "kpis": {
                "turnos_atendidos": atendidos,
                "turnos_cancelados": cancelados,
                "turnos_ausentes": ausentes,
                "total_consultas_realizadas": len(consultas),
                "porcentaje_consultas_con_orden": porcentaje_orden,
            },
            "comparacion_consultas_ordenes": [
                {"estado": "Consultas realizadas", "cantidad": len(consultas)},
                {"estado": "Con orden", "cantidad": con_orden},
            ],
            "actividad_por_hora": self._agrupar_por_hora(consultas),
            "rendimiento_veterinarios": actividad_veterinarios,
            "distribucion_estados_turno": distribucion,
            "filtros_disponibles": {
                "veterinarios": ["Todos"] + vets_disponibles,
                "especialidades": ["Todas"] + especialidades,
                "estados_turno": ["Todos", "Atendido", "Ausente", "Cancelado"],
                "derivaciones": ["Todos", "Con Derivación", "Sin Derivación"],
            },
        }

    def _recopilar_detalles_clinicos(self) -> list[dict[str, Any]]:
        registros = []
        consultas_en_turno: set[int] = set()
        for turno in self.db.scalars(select(Turno)).all():
            consulta = turno.consultations[0] if turno.consultations else None
            if consulta:
                consultas_en_turno.add(consulta.id)
            orden = self.db.scalar(select(OrdenAnalisis).where(OrdenAnalisis.consulta_id == consulta.id)) if consulta else None
            estado = (
                "Atendido" if turno.status in {"atendido", "completado"}
                else "Ausente" if turno.status in {"ausente", "no_presentado"}
                else "Cancelado" if turno.status == "cancelado"
                else "Atendido" if consulta else "Pendiente"
            )
            fecha = consulta.attended_at if consulta else turno.scheduled_at
            registros.append({
                "turno_id": str(turno.id),
                "fecha_hora": fecha.strftime("%Y-%m-%d %H:%M") if fecha else "",
                "hora_consulta": consulta.attended_at.hour if consulta else None,
                "veterinario_nombre": turno.veterinarian.full_name if turno.veterinarian else "Sin dato",
                "especialidad": turno.veterinarian.specialty if turno.veterinarian and turno.veterinarian.specialty else "Sin especialidad",
                "estado_turno": estado,
                "consulta_realizada": consulta is not None,
                "derivo_laboratorio": orden is not None,
            })

        for consulta in self.db.scalars(select(Consulta)).all():
            if consulta.id in consultas_en_turno:
                continue
            orden = self.db.scalar(select(OrdenAnalisis).where(OrdenAnalisis.consulta_id == consulta.id))
            registros.append({
                "turno_id": "Sin turno",
                "fecha_hora": consulta.attended_at.strftime("%Y-%m-%d %H:%M") if consulta.attended_at else "",
                "hora_consulta": consulta.attended_at.hour if consulta.attended_at else None,
                "veterinario_nombre": consulta.veterinarian.full_name if consulta.veterinarian else "Sin dato",
                "especialidad": consulta.veterinarian.specialty if consulta.veterinarian and consulta.veterinarian.specialty else "Sin especialidad",
                "estado_turno": "Sin turno",
                "consulta_realizada": True,
                "derivo_laboratorio": orden is not None,
            })
        return registros

    @staticmethod
    def _agrupar_por_hora(consultas: list[dict[str, Any]]) -> list[dict[str, int]]:
        conteo: dict[int, int] = {}
        for consulta in consultas:
            hora = consulta.get("hora_consulta")
            if hora is not None:
                conteo[hora] = conteo.get(hora, 0) + 1
        return [{"hora": hora, "cantidad": conteo[hora]} for hora in sorted(conteo)]

    def exportar_excel_rendimiento_clinico(self, datos: dict[str, Any]) -> bytes:
        return exportar_reporte_excel("Actividad médica y consultas", datos, [("Actividad de turnos", "distribucion_estados_turno"), ("Consultas por hora", "actividad_por_hora"), ("Consultas y órdenes", "comparacion_consultas_ordenes"), ("Consultas por profesional", "rendimiento_veterinarios")])


    def exportar_pdf_rendimiento_clinico(self, datos: dict[str, Any]) -> bytes:
        return exportar_reporte_pdf("Actividad médica y consultas", datos, [("Actividad de turnos", "distribucion_estados_turno"), ("Consultas por hora", "actividad_por_hora"), ("Consultas y órdenes", "comparacion_consultas_ordenes"), ("Consultas por profesional", "rendimiento_veterinarios")])


    def enviar_reporte_rendimiento_email(
        self,
        destinatario: str,
        asunto: str | None = None,
        incluir_pdf: bool = True,
        incluir_excel: bool = True,
        datos: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        datos = datos or self.generar_reporte_rendimiento_clinico()
        return enviar_reporte_email_adjuntos(destinatario, asunto, incluir_pdf, incluir_excel, datos, "reporte_actividad_medica", self.exportar_pdf_rendimiento_clinico, self.exportar_excel_rendimiento_clinico)
