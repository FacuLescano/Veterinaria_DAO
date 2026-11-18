"""Servicio especializado para el Reporte 4: Eficacia Diagnóstica & Hallazgos Críticos.

Correlaciona diagnósticos presuntivos clínicos con determinaciones analíticas de laboratorio,
calculando tasas de positividad, distribución epidemiológica por especie y grupo etario,
y ranking de analitos fuera de rango.
"""

from __future__ import annotations

from datetime import datetime, timezone
import io
import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.orden_analisis import DetalleOrdenAnalisis, OrdenAnalisis, TipoAnalisis
from app.models.paciente import Consulta, Mascota, Responsable, Veterinario
from app.models.recepcion import ResultadoAnalisis
from app.services.correo_service import ServicioCorreo
from app.services.reportes.base import RUTA_LOGO, fecha_hora_argentina_str

logger = logging.getLogger(__name__)


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
        """Calcula métricas, tablas de contingencia y registros detallados para el Reporte 4."""
        detalles = self._recopilar_detalles_eficacia()

        # Opciones de filtros disponibles
        especies_disponibles = sorted(list({d["especie"] for d in detalles if d.get("especie")}))
        grupos_disponibles = sorted(list({d["grupo_etario"] for d in detalles if d.get("grupo_etario")}))
        tipos_disponibles = sorted(list({d["tipo_analisis"] for d in detalles if d.get("tipo_analisis")}))

        # Aplicar filtros
        if fecha_desde:
            detalles = [d for d in detalles if d["fecha_emision"][:10] >= fecha_desde[:10]]
        if fecha_hasta:
            detalles = [d for d in detalles if d["fecha_emision"][:10] <= fecha_hasta[:10]]
        if especie_filtro and especie_filtro != "Todas":
            detalles = [d for d in detalles if d["especie"].strip().lower() == especie_filtro.strip().lower()]
        if grupo_etario_filtro and grupo_etario_filtro != "Todos":
            detalles = [d for d in detalles if d["grupo_etario"].strip().lower() == grupo_etario_filtro.strip().lower()]
        if estado_diagnostico_filtro and estado_diagnostico_filtro != "Todos":
            detalles = [d for d in detalles if d["estado_diagnostico"].strip().lower() == estado_diagnostico_filtro.strip().lower()]
        if tipo_analisis_filtro and tipo_analisis_filtro != "Todos":
            detalles = [d for d in detalles if d["tipo_analisis"].strip().lower() == tipo_analisis_filtro.strip().lower()]

        total_estudios = len(detalles)
        estudios_evaluables = [d for d in detalles if d["estado_diagnostico"] != "Sin datos interpretables"]
        hallazgos_criticos = sum(1 for d in estudios_evaluables if d["estado_diagnostico"] == "Hallazgo Patológico")
        fisiologicos_normales = sum(1 for d in estudios_evaluables if d["estado_diagnostico"] == "Fisiológico Normal")

        tasa_positividad = round((hallazgos_criticos / len(estudios_evaluables)) * 100, 1) if estudios_evaluables else 0.0
        # El modelo no registra una conclusión veterinaria posterior con la que
        # comparar el diagnóstico presuntivo; por ahora esta métrica no es calculable.
        tasa_concordancia = None
        especies_unicas = len({d["especie"] for d in detalles})

        # Desglose por Especie
        por_especie: dict[str, list[dict[str, Any]]] = {}
        for d in detalles:
            por_especie.setdefault(d["especie"], []).append(d)

        desglose_especies = []
        for esp, items in por_especie.items():
            tot_esp = len(items)
            pat_esp = sum(1 for i in items if i["estado_diagnostico"] == "Hallazgo Patológico")
            evaluables = [i for i in items if i["estado_diagnostico"] != "Sin datos interpretables"]
            norm_esp = sum(1 for i in evaluables if i["estado_diagnostico"] == "Fisiológico Normal")
            pct_pos = round((pat_esp / len(evaluables)) * 100, 1) if evaluables else 0.0

            # Patología predominante
            analitos_alterados: list[str] = []
            for i in items:
                analitos_alterados.extend(i.get("parametros_alterados", []))
            predom = max(set(analitos_alterados), key=analitos_alterados.count) if analitos_alterados else "Sin alteraciones críticas"

            desglose_especies.append({
                "especie": esp,
                "total_estudios": tot_esp,
                "patologicos": pat_esp,
                "normales": norm_esp,
                "tasa_positividad_porcentaje": pct_pos,
                "patologia_predominante": predom,
            })

        desglose_especies.sort(key=lambda x: x["total_estudios"], reverse=True)

        # Desglose por Grupo Etario
        por_etario: dict[str, list[dict[str, Any]]] = {}
        for d in detalles:
            por_etario.setdefault(d["grupo_etario"], []).append(d)

        orden_etario = ["Cachorro / Joven", "Adulto", "Geriátrico", "Sin dato"]
        desglose_etario = []
        for grp in orden_etario:
            items_grp = por_etario.get(grp, [])
            tot_g = len(items_grp)
            pat_g = sum(1 for i in items_grp if i["estado_diagnostico"] == "Hallazgo Patológico")
            evaluables = [i for i in items_grp if i["estado_diagnostico"] != "Sin datos interpretables"]
            norm_g = sum(1 for i in evaluables if i["estado_diagnostico"] == "Fisiológico Normal")
            pct_g = round((pat_g / len(evaluables)) * 100, 1) if evaluables else 0.0
            desglose_etario.append({
                "grupo_etario": grp,
                "total_estudios": tot_g,
                "patologicos": pat_g,
                "normales": norm_g,
                "tasa_positividad_porcentaje": pct_g,
            })

        # Top de Analitos Críticos Fuera de Rango
        analitos_conteo: dict[str, dict[str, Any]] = {}
        for d in detalles:
            for p in d.get("lista_parametros_alerta", []):
                nombre_p = p.get("parametro", "Desconocido")
                if nombre_p not in analitos_conteo:
                    analitos_conteo[nombre_p] = {
                        "parametro": nombre_p,
                        "tipo_analisis": d["tipo_analisis"],
                        "frecuencia_alerta": 0,
                        "alertas_altas": 0,
                        "alertas_bajas": 0,
                    }
                analitos_conteo[nombre_p]["frecuencia_alerta"] += 1
                if p.get("alerta") == "Alto":
                    analitos_conteo[nombre_p]["alertas_altas"] += 1
                elif p.get("alerta") == "Bajo":
                    analitos_conteo[nombre_p]["alertas_bajas"] += 1

        top_analitos = []
        total_alertas_globales = sum(a["frecuencia_alerta"] for a in analitos_conteo.values())
        for a in analitos_conteo.values():
            pct_incidencia = (
                round((a["frecuencia_alerta"] / total_alertas_globales) * 100, 1)
                if total_alertas_globales > 0
                else 0.0
            )
            tipo_predom = "Alto" if a["alertas_altas"] >= a["alertas_bajas"] else "Bajo"
            top_analitos.append({
                "parametro": a["parametro"],
                "tipo_analisis": a["tipo_analisis"],
                "frecuencia_alerta": a["frecuencia_alerta"],
                "porcentaje_incidencia": pct_incidencia,
                "tipo_alerta_predominante": tipo_predom,
            })

        top_analitos.sort(key=lambda x: x["frecuencia_alerta"], reverse=True)

        # Distribución de Severidad
        severidad_counts = {"Crítico": 0, "Moderado": 0, "Normal": 0}
        for d in detalles:
            sev = d.get("severidad", "Normal")
            severidad_counts[sev] = severidad_counts.get(sev, 0) + 1

        distribucion_severidad = [
            {
                "severidad": k,
                "cantidad": v,
                "porcentaje": round((v / total_estudios) * 100, 1) if total_estudios > 0 else 0.0,
            }
            for k, v in severidad_counts.items()
        ]

        return {
            "fecha_generacion": fecha_hora_argentina_str(),
            "kpis": {
                "total_estudios_procesados": total_estudios,
                "total_estudios_evaluables": len(estudios_evaluables),
                "total_con_hallazgos_criticos": hallazgos_criticos,
                "total_fisiologicos_normales": fisiologicos_normales,
                "tasa_positividad_porcentaje": tasa_positividad,
                "tasa_concordancia_diagnostica": tasa_concordancia,
                "total_especies_auditadas": especies_unicas,
            },
            "desglose_por_especie": desglose_especies,
            "desglose_por_grupo_etario": desglose_etario,
            "top_analitos_criticos": top_analitos,
            "distribucion_severidad": distribucion_severidad,
            "detalles_diagnosticos": detalles,
            "filtros_disponibles": {
                "especies": ["Todas"] + especies_disponibles,
                "grupos_etarios": ["Todos"] + grupos_disponibles,
                "estados_diagnosticos": ["Todos", "Hallazgo Patológico", "Fisiológico Normal"],
                "tipos_analisis": ["Todos"] + tipos_disponibles,
            },
        }

    def _recopilar_detalles_eficacia(self) -> list[dict[str, Any]]:
        """Recopila resultados analíticos cruzándolos con órdenes y consultas."""
        registros: list[dict[str, Any]] = []

        try:
            resultados_db = self.db.scalars(select(ResultadoAnalisis)).all()
            for r in resultados_db:
                orden = None
                if r.orden_id:
                    try:
                        orden = self.db.get(OrdenAnalisis, int(r.orden_id))
                    except (ValueError, TypeError):
                        pass

                consulta = orden.consulta if orden else None
                pet = consulta.pet if consulta else None
                tutor = pet.responsible if pet else None
                vet = orden.veterinario if orden else (consulta.veterinarian if consulta else None)

                # Calcular edad y grupo etario
                edad_anios = None
                if pet and pet.birth_date:
                    hoy = datetime.now().date()
                    edad_anios = max(0, hoy.year - pet.birth_date.year)

                if edad_anios is None:
                    grupo_etario = "Sin dato"
                elif edad_anios < 1:
                    grupo_etario = "Cachorro / Joven"
                elif edad_anios <= 7:
                    grupo_etario = "Adulto"
                else:
                    grupo_etario = "Geriátrico"

                tipo_estudio = "Sin dato"
                if orden and orden.detalles:
                    tipo_estudio = orden.detalles[0].tipo_analisis.nombre if orden.detalles[0].tipo_analisis else "Sin dato"

                # Interpretar datos de laboratorio
                datos = r.datos or {}
                valores = datos.get("valores", [])
                conclusion = datos.get("conclusionDiagnostica", r.interpretacion_clinica or "Sin conclusión registrada")

                alertas = [v for v in valores if isinstance(v, dict) and v.get("alerta") in {"Alto", "Bajo", "Crítico"}]
                tiene_datos_interpretables = bool(valores)
                tiene_patologia = len(alertas) > 0

                severidad = "Sin dato" if not tiene_datos_interpretables else "Normal"
                if tiene_patologia:
                    tiene_critico = any(v.get("alerta") == "Crítico" or "Glóbulos blancos" in v.get("parametro", "") for v in alertas)
                    severidad = "Crítico" if tiene_critico else "Moderado"

                diag_presuntivo = consulta.diagnosis if consulta and consulta.diagnosis else "Sin dato"
                concordancia = "No evaluable"

                resumen_params = []
                params_alterados = []
                for v in valores:
                    if isinstance(v, dict):
                        p_nom = v.get("parametro", "")
                        p_val = v.get("valor", "")
                        p_uni = v.get("unidad", "")
                        p_alt = v.get("alerta", "Normal")
                        if p_alt != "Normal":
                            resumen_params.append(f"{p_nom}: {p_val} {p_uni} ({p_alt})")
                            params_alterados.append(p_nom)

                registros.append({
                    "resultado_id": f"RES-{r.id[:8]}",
                    "orden_codigo": f"ORD-{orden.id:04d}" if orden else "Sin dato",
                    "fecha_emision": r.fecha_recepcion.strftime("%Y-%m-%d %H:%M") if r.fecha_recepcion else "Sin dato",
                    "paciente_nombre": pet.name if pet else "Sin dato",
                    "especie": pet.species if pet else "Sin dato",
                    "raza": pet.breed if pet and pet.breed else "Sin dato",
                    "edad_anios": edad_anios,
                    "grupo_etario": grupo_etario,
                    "tutor_nombre": tutor.full_name if tutor else "Sin dato",
                    "veterinario_nombre": vet.full_name if vet else "Sin dato",
                    "motivo_consulta": consulta.reason if consulta else "Sin dato",
                    "diagnostico_presuntivo": diag_presuntivo,
                    "tipo_analisis": tipo_estudio,
                    "parametros_resumen": "; ".join(resumen_params) if resumen_params else "Sin parámetros interpretables" if not tiene_datos_interpretables else "Todos los parámetros dentro de rango",
                    "parametros_alterados": params_alterados,
                    "lista_parametros_alerta": alertas,
                    "estado_diagnostico": "Hallazgo Patológico" if tiene_patologia else "Fisiológico Normal" if tiene_datos_interpretables else "Sin datos interpretables",
                    "severidad": severidad,
                    "concordancia": concordancia,
                    "conclusion_laboratorio": conclusion,
                })
        except Exception as err:
            logger.warning("Fallo al consultar base de datos para Reporte 4 (%s)", err)

        return registros

    def exportar_excel_eficacia_diagnostica(self, datos: dict[str, Any]) -> bytes:
        """Genera el libro Excel profesional (.xlsx) con 2 hojas y logotipo oficial."""
        import openpyxl
        from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
        from openpyxl.utils import get_column_letter

        wb = openpyxl.Workbook()
        ws1 = wb.active
        ws1.title = "Eficacia y Epidemiología"
        ws1.views.sheetView[0].showGridLines = True

        fill_header = PatternFill(start_color="2D5864", end_color="2D5864", fill_type="solid")
        font_header = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        fill_kpi = PatternFill(start_color="FAF6EF", end_color="FAF6EF", fill_type="solid")
        font_kpi_num = Font(name="Calibri", size=16, bold=True, color="2D5864")
        thin_border = Border(
            left=Side(style="thin", color="D1D5DB"),
            right=Side(style="thin", color="D1D5DB"),
            top=Side(style="thin", color="D1D5DB"),
            bottom=Side(style="thin", color="D1D5DB"),
        )
        fill_critico = PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid")
        fill_normal = PatternFill(start_color="DCFCE7", end_color="DCFCE7", fill_type="solid")
        fill_moderado = PatternFill(start_color="FEF3C7", end_color="FEF3C7", fill_type="solid")

        # Agregar logo si existe
        if RUTA_LOGO.exists():
            try:
                from openpyxl.drawing.image import Image as OpenpyxlImage
                img_logo = OpenpyxlImage(str(RUTA_LOGO))
                img_logo.width = 54
                img_logo.height = 54
                ws1.add_image(img_logo, "A1")
                ws1.column_dimensions["A"].width = 11
            except Exception as err:
                logger.warning("No se pudo agregar logo a Excel: %s", err)

        ws1.merge_cells("B1:H1")
        ws1["B1"] = "PATITAS & CO. — AUDITORÍA DE EFICACIA DIAGNÓSTICA Y HALLAZGOS CRÍTICOS"
        ws1["B1"].font = Font(name="Calibri", size=14, bold=True, color="2D5864")
        ws1["B1"].alignment = Alignment(horizontal="left", vertical="center")

        ws1.merge_cells("B2:H2")
        ws1["B2"] = f"Reporte 4: Correlación Clínica, Positividad Analítica y Epidemiología Veterinaria (Generado: {datos.get('fecha_generacion', '')})"
        ws1["B2"].font = Font(name="Calibri", size=11, italic=True, color="6B7280")

        ws1.row_dimensions[1].height = 24
        ws1.row_dimensions[2].height = 20
        ws1.row_dimensions[3].height = 10

        # Bloque de KPIs
        kpis = datos["kpis"]
        kpi_cards = [
            ("Estudios Procesados", f"{kpis['total_estudios_procesados']}"),
            ("Hallazgos Patológicos", f"{kpis['total_con_hallazgos_criticos']}"),
            ("Fisiológicos Normales", f"{kpis['total_fisiologicos_normales']}"),
            ("Tasa Positividad", f"{kpis['tasa_positividad_porcentaje']}%"),
            ("Concordancia Diagnóstica", f"{kpis['tasa_concordancia_diagnostica']}%"),
            ("Especies Auditadas", f"{kpis['total_especies_auditadas']}"),
        ]

        for col_idx, (titulo, valor) in enumerate(kpi_cards, start=1):
            cell_title = ws1.cell(row=4, column=col_idx, value=titulo)
            cell_title.font = Font(name="Calibri", size=9, bold=True, color="4B5563")
            cell_title.fill = fill_kpi
            cell_title.alignment = Alignment(horizontal="center", vertical="center")
            cell_title.border = thin_border

            cell_val = ws1.cell(row=5, column=col_idx, value=valor)
            cell_val.font = font_kpi_num
            cell_val.fill = fill_kpi
            cell_val.alignment = Alignment(horizontal="center", vertical="center")
            cell_val.border = thin_border

        ws1.row_dimensions[4].height = 18
        ws1.row_dimensions[5].height = 28

        # Tabla 1: Desglose por Especie
        ws1.cell(row=7, column=1, value="DISTRIBUCIÓN EPIDEMIOLÓGICA POR ESPECIE").font = Font(name="Calibri", size=11, bold=True, color="2D5864")
        headers_esp = ["Especie", "Total Estudios", "Patológicos (Positivos)", "Normales (Negativos)", "Tasa Positividad (%)", "Patología / Analito Predominante"]

        for col_idx, h in enumerate(headers_esp, start=1):
            cell = ws1.cell(row=8, column=col_idx, value=h)
            cell.fill = fill_header
            cell.font = font_header
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = thin_border

        row_curr = 9
        for esp in datos.get("desglose_por_especie", []):
            ws1.cell(row=row_curr, column=1, value=esp["especie"]).border = thin_border
            ws1.cell(row=row_curr, column=2, value=esp["total_estudios"]).border = thin_border
            ws1.cell(row=row_curr, column=3, value=esp["patologicos"]).border = thin_border
            ws1.cell(row=row_curr, column=4, value=esp["normales"]).border = thin_border
            cell_pct = ws1.cell(row=row_curr, column=5, value=f"{esp['tasa_positividad_porcentaje']}%")
            cell_pct.border = thin_border
            cell_pct.alignment = Alignment(horizontal="center")
            ws1.cell(row=row_curr, column=6, value=esp["patologia_predominante"]).border = thin_border
            row_curr += 1

        # Tabla 2: Top de Analitos Críticos
        row_curr += 2
        ws1.cell(row=row_curr, column=1, value="TOP DE PARÁMETROS CRÍTICOS FUERA DE RANGO").font = Font(name="Calibri", size=11, bold=True, color="2D5864")
        row_curr += 1

        headers_ana = ["Parámetro / Analito", "Tipo de Estudio", "Frecuencia Alertas", "Incidencia (%)", "Tendencia"]
        for col_idx, h in enumerate(headers_ana, start=1):
            cell = ws1.cell(row=row_curr, column=col_idx, value=h)
            cell.fill = fill_header
            cell.font = font_header
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = thin_border

        row_curr += 1
        for ana in datos.get("top_analitos_criticos", []):
            ws1.cell(row=row_curr, column=1, value=ana["parametro"]).border = thin_border
            ws1.cell(row=row_curr, column=2, value=ana["tipo_analisis"]).border = thin_border
            ws1.cell(row=row_curr, column=3, value=ana["frecuencia_alerta"]).border = thin_border
            ws1.cell(row=row_curr, column=4, value=f"{ana['porcentaje_incidencia']}%").border = thin_border
            cell_tend = ws1.cell(row=row_curr, column=5, value=ana["tipo_alerta_predominante"])
            cell_tend.border = thin_border
            cell_tend.alignment = Alignment(horizontal="center")
            row_curr += 1

        # Autoajuste de columnas ws1
        for col in ws1.columns:
            max_len = 0
            col_letter = get_column_letter(col[0].column)
            for cell in col:
                val_str = str(cell.value or "")
                if "\n" in val_str:
                    val_str = max(val_str.split("\n"), key=len)
                if len(val_str) > max_len and cell.row > 2:
                    max_len = len(val_str)
            ws1.column_dimensions[col_letter].width = max(max_len + 3, 12)

        # Hoja 2: Detalle Diagnóstico
        ws2 = wb.create_sheet(title="Auditoría de Hallazgos")
        ws2.views.sheetView[0].showGridLines = True

        headers_det = [
            "ID Resultado",
            "Código Orden",
            "Fecha Emisión",
            "Paciente",
            "Especie / Raza",
            "Grupo Etario",
            "Tutor",
            "Médico Veterinario",
            "Diagnóstico Presuntivo",
            "Tipo de Análisis",
            "Estado Diagnóstico",
            "Severidad",
            "Concordancia",
            "Parámetros Alterados / Alertas",
            "Conclusión Clínica del Laboratorio",
        ]

        for col_idx, h in enumerate(headers_det, start=1):
            cell = ws2.cell(row=1, column=col_idx, value=h)
            cell.fill = fill_header
            cell.font = font_header
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = thin_border

        ws2.row_dimensions[1].height = 25

        row_det = 2
        for d in datos.get("detalles_diagnosticos", []):
            ws2.cell(row=row_det, column=1, value=d["resultado_id"]).border = thin_border
            ws2.cell(row=row_det, column=2, value=d["orden_codigo"]).border = thin_border
            ws2.cell(row=row_det, column=3, value=d["fecha_emision"]).border = thin_border
            ws2.cell(row=row_det, column=4, value=d["paciente_nombre"]).border = thin_border
            ws2.cell(row=row_det, column=5, value=f"{d['especie']} ({d.get('raza', '')})").border = thin_border
            ws2.cell(row=row_det, column=6, value=f"{d['grupo_etario']} ({d['edad_anios']}a)").border = thin_border
            ws2.cell(row=row_det, column=7, value=d["tutor_nombre"]).border = thin_border
            ws2.cell(row=row_det, column=8, value=d["veterinario_nombre"]).border = thin_border
            ws2.cell(row=row_det, column=9, value=d["diagnostico_presuntivo"]).border = thin_border
            ws2.cell(row=row_det, column=10, value=d["tipo_analisis"]).border = thin_border

            # Estado Diagnóstico con color
            c_est = ws2.cell(row=row_det, column=11, value=d["estado_diagnostico"])
            c_est.border = thin_border
            c_est.alignment = Alignment(horizontal="center")
            if d["estado_diagnostico"] == "Hallazgo Patológico":
                c_est.fill = fill_critico
            else:
                c_est.fill = fill_normal

            # Severidad
            c_sev = ws2.cell(row=row_det, column=12, value=d["severidad"])
            c_sev.border = thin_border
            c_sev.alignment = Alignment(horizontal="center")
            if d["severidad"] == "Crítico":
                c_sev.fill = fill_critico
            elif d["severidad"] == "Moderado":
                c_sev.fill = fill_moderado
            else:
                c_sev.fill = fill_normal

            ws2.cell(row=row_det, column=13, value=d["concordancia"]).border = thin_border
            ws2.cell(row=row_det, column=14, value=d["parametros_resumen"]).border = thin_border
            ws2.cell(row=row_det, column=15, value=d["conclusion_laboratorio"]).border = thin_border

            row_det += 1

        for col in ws2.columns:
            max_len = 0
            col_letter = get_column_letter(col[0].column)
            for cell in col:
                val_str = str(cell.value or "")
                if "\n" in val_str:
                    val_str = max(val_str.split("\n"), key=len)
                if len(val_str) > max_len and cell.row > 1:
                    max_len = len(val_str)
            ws2.column_dimensions[col_letter].width = max(min(max_len + 3, 40), 12)

        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        return buffer.getvalue()

    def exportar_pdf_eficacia_diagnostica(self, datos: dict[str, Any]) -> bytes:
        """Genera el acta oficial en PDF apaisado con reporte epidemiológico y trazabilidad."""
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(A4),
            rightMargin=25,
            leftMargin=25,
            topMargin=25,
            bottomMargin=25,
        )

        styles = getSampleStyleSheet()
        style_title = ParagraphStyle(
            "TitleStyle4",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=16,
            textColor=colors.HexColor("#2D5864"),
            spaceAfter=2,
        )
        style_subtitle = ParagraphStyle(
            "SubTitleStyle4",
            parent=styles["Normal"],
            fontSize=9,
            leading=11,
            textColor=colors.HexColor("#6B7280"),
            spaceAfter=10,
        )
        style_cell = ParagraphStyle("Cell4", parent=styles["Normal"], fontSize=8, leading=10)
        style_cell_bold = ParagraphStyle("CellBold4", parent=styles["Normal"], fontSize=8, leading=10, fontName="Helvetica-Bold")
        style_cell_header = ParagraphStyle("CellHeader4", parent=styles["Normal"], fontSize=8, leading=10, fontName="Helvetica-Bold", textColor=colors.white)

        elements = []

        if RUTA_LOGO.exists():
            try:
                from reportlab.platypus import Image as RLImage
                logo_rl = RLImage(str(RUTA_LOGO), width=44, height=44)
                header_table = Table(
                    [[
                        logo_rl,
                        [
                            Paragraph("PATITAS & CO. — AUDITORÍA DE EFICACIA DIAGNÓSTICA Y HALLAZGOS CRÍTICOS", style_title),
                            Paragraph(f"Reporte 4: Positividad, Correlación Presuntiva y Epidemiología Veterinaria · Generado el {datos.get('fecha_generacion', '')}", style_subtitle),
                        ]
                    ]],
                    colWidths=[52, 680]
                )
                header_table.setStyle(TableStyle([
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                ]))
                elements.append(header_table)
            except Exception as err:
                logger.warning("Error al adjuntar logo a PDF: %s", err)
                elements.append(Paragraph("PATITAS & CO. — AUDITORÍA DE EFICACIA DIAGNÓSTICA", style_title))
                elements.append(Paragraph(f"Reporte 4: Positividad y Correlación Presuntiva · Generado el {datos.get('fecha_generacion', '')}", style_subtitle))
        else:
            elements.append(Paragraph("PATITAS & CO. — AUDITORÍA DE EFICACIA DIAGNÓSTICA", style_title))
            elements.append(Paragraph(f"Reporte 4: Positividad y Correlación Presuntiva · Generado el {datos.get('fecha_generacion', '')}", style_subtitle))

        # Tarjetas KPIs
        kpis = datos["kpis"]
        kpi_data = [
            ["Estudios Procesados", "Hallazgos Patológicos", "Fisiológicos Normales", "Tasa Positividad", "Concordancia Diagnóstica", "Especies Auditadas"],
            [
                str(kpis["total_estudios_procesados"]),
                str(kpis["total_con_hallazgos_criticos"]),
                str(kpis["total_fisiologicos_normales"]),
                f"{kpis['tasa_positividad_porcentaje']}%",
                f"{kpis['tasa_concordancia_diagnostica']}%",
                str(kpis["total_especies_auditadas"]),
            ],
        ]
        t_kpi = Table(kpi_data, colWidths=[122] * 6)
        t_kpi.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FAF6EF")),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#4B5563")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 8),
            ("TEXTCOLOR", (0, 1), (-1, 1), colors.HexColor("#2D5864")),
            ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 1), (-1, 1), 13),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
        ]))
        elements.append(t_kpi)
        elements.append(Spacer(1, 12))

        # Tabla Resumen por Especie
        elements.append(Paragraph("<b>DISTRIBUCIÓN EPIDEMIOLÓGICA POR ESPECIE Y GRUPO ETARIO</b>", style_cell_bold))
        elements.append(Spacer(1, 4))

        esp_rows = [[
            Paragraph("Especie", style_cell_header),
            Paragraph("Total Estudios", style_cell_header),
            Paragraph("Patológicos", style_cell_header),
            Paragraph("Normales", style_cell_header),
            Paragraph("Positividad (%)", style_cell_header),
            Paragraph("Patología / Analito Predominante", style_cell_header),
        ]]
        for esp in datos.get("desglose_por_especie", []):
            esp_rows.append([
                Paragraph(esp["especie"], style_cell_bold),
                Paragraph(str(esp["total_estudios"]), style_cell),
                Paragraph(str(esp["patologicos"]), style_cell),
                Paragraph(str(esp["normales"]), style_cell),
                Paragraph(f"{esp['tasa_positividad_porcentaje']}%", style_cell_bold),
                Paragraph(esp["patologia_predominante"], style_cell),
            ])

        t_esp = Table(esp_rows, colWidths=[90, 80, 80, 80, 90, 312])
        t_esp.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2D5864")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F9FAFB")]),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        elements.append(t_esp)
        elements.append(Spacer(1, 12))

        # Tabla Detallada de Casos Clínicos
        elements.append(Paragraph("<b>AUDITORÍA CLÍNICA DE RESULTADOS Y CORRELACIÓN DIAGNÓSTICA</b>", style_cell_bold))
        elements.append(Spacer(1, 4))

        det_rows = [[
            Paragraph("ID / Paciente", style_cell_header),
            Paragraph("Especie / Edad", style_cell_header),
            Paragraph("Estudio", style_cell_header),
            Paragraph("Diagnóstico Presuntivo", style_cell_header),
            Paragraph("Parámetros Críticos / Alertas", style_cell_header),
            Paragraph("Estado / Severidad", style_cell_header),
            Paragraph("Conclusión del Laboratorio", style_cell_header),
        ]]

        for d in datos.get("detalles_diagnosticos", [])[:14]:  # Top 14 en vista PDF
            det_rows.append([
                Paragraph(f"<b>{d['paciente_nombre']}</b><br/><font color='#6B7280' size='6'>{d['resultado_id']} · {d['tutor_nombre']}</font>", style_cell),
                Paragraph(f"{d['especie']}<br/><font color='#6B7280' size='6'>{d['grupo_etario']} ({d['edad_anios']}a)</font>", style_cell),
                Paragraph(f"<b>{d['tipo_analisis']}</b>", style_cell),
                Paragraph(d["diagnostico_presuntivo"], style_cell),
                Paragraph(d["parametros_resumen"], style_cell),
                Paragraph(f"<b>{d['estado_diagnostico']}</b><br/><font color='#6B7280' size='6'>Severidad: {d['severidad']}</font>", style_cell),
                Paragraph(d["conclusion_laboratorio"], style_cell),
            ])

        t_det = Table(det_rows, colWidths=[90, 80, 100, 110, 130, 90, 132])
        t_det.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2D5864")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F9FAFB")]),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        elements.append(t_det)

        elements.append(Spacer(1, 8))
        elements.append(Paragraph(
            "<font color='#6B7280' size='7'>* Certificación de Calidad Analítica según directrices de Patología Clínica Veterinaria. Los valores de referencia corresponden a las matrices hematológicas y bioquímicas específicas validadas para cada especie.</font>",
            style_cell
        ))

        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()

    def enviar_reporte_eficacia_email(
        self,
        destinatario: str,
        asunto: str | None = None,
        incluir_pdf: bool = True,
        incluir_excel: bool = True,
        datos: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Envía el reporte de Eficacia Diagnóstica por correo electrónico con adjuntos."""
        if not datos:
            datos = self.generar_reporte_eficacia_diagnostica()

        asunto_final = asunto or "Reporte de Eficacia Diagnóstica y Hallazgos Críticos — Patitas & Co."

        kpis = datos["kpis"]
        filas_esp_html = ""
        for esp in datos.get("desglose_por_especie", []):
            filas_esp_html += f"""
            <tr>
              <td style="padding: 6px 10px; border-bottom: 1px solid #E5E7EB; font-weight: bold; color: #111827;">{esp['especie']}</td>
              <td style="padding: 6px 10px; border-bottom: 1px solid #E5E7EB; text-align: center;">{esp['total_estudios']}</td>
              <td style="padding: 6px 10px; border-bottom: 1px solid #E5E7EB; text-align: center; color: #B91C1C; font-weight: bold;">{esp['patologicos']}</td>
              <td style="padding: 6px 10px; border-bottom: 1px solid #E5E7EB; text-align: center; color: #047857;">{esp['normales']}</td>
              <td style="padding: 6px 10px; border-bottom: 1px solid #E5E7EB; text-align: center; font-weight: bold;">{esp['tasa_positividad_porcentaje']}%</td>
              <td style="padding: 6px 10px; border-bottom: 1px solid #E5E7EB; color: #4B5563;">{esp['patologia_predominante']}</td>
            </tr>
            """

        cuerpo_texto = (
            f"PATITAS & CO. — AUDITORÍA DE EFICACIA DIAGNÓSTICA\n"
            f"Reporte 4: Positividad, Correlación Presuntiva y Epidemiología Veterinaria\n\n"
            f"Resumen de Indicadores Clave:\n"
            f"- Total Estudios Procesados: {kpis['total_estudios_procesados']}\n"
            f"- Hallazgos Patológicos / Críticos: {kpis['total_con_hallazgos_criticos']}\n"
            f"- Tasa de Positividad Global: {kpis['tasa_positividad_porcentaje']}%\n"
            f"- Tasa de Concordancia Diagnóstica: {kpis['tasa_concordancia_diagnostica']}%\n"
            f"- Fisiológicos Normales: {kpis['total_fisiologicos_normales']}\n"
            f"- Especies Auditadas: {kpis['total_especies_auditadas']}\n"
        )

        cuerpo_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset="utf-8">
          <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #F8F6F2; margin: 0; padding: 20px; color: #374151; }}
            .container {{ max-width: 680px; margin: 0 auto; background: #ffffff; border-radius: 12px; border: 1px solid #E7E2DA; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); }}
            .header {{ background-color: #2D5864; color: #ffffff; padding: 24px; text-align: left; }}
            .content {{ padding: 24px; }}
            .table {{ width: 100%; border-collapse: collapse; font-size: 11px; margin-top: 12px; }}
            .table th {{ background-color: #FAF6EF; color: #2D5864; font-weight: bold; padding: 8px 10px; text-align: left; border-bottom: 2px solid #E7E2DA; }}
            .footer {{ background-color: #FAF8F5; padding: 16px 24px; font-size: 11px; color: #9CA3AF; text-align: center; border-top: 1px solid #E7E2DA; }}
          </style>
        </head>
        <body>
          <div class="container">
            <div class="header">
              <table style="width: 100%; border: none;">
                <tr>
                  <td style="width: 50px; vertical-align: middle;">
                    <img src="cid:logo_patitas" alt="Patitas & Co." style="width: 44px; height: 44px; border-radius: 8px; background: white; padding: 2px;" />
                  </td>
                  <td style="vertical-align: middle; padding-left: 12px;">
                    <h1 style="color: #ffffff; margin: 0; font-size: 17px;">PATITAS & CO. — EFICACIA DIAGNÓSTICA</h1>
                    <p style="color: #E7E2DA; margin: 3px 0 0; font-size: 11px;">Reporte 4: Auditoría de Positividad y Hallazgos Críticos por Especie</p>
                  </td>
                </tr>
              </table>
            </div>

            <div class="content">
              <p style="font-size: 13px; margin-top: 0;">Estimado/a colega,</p>
              <p style="font-size: 12px; line-height: 1.5; color: #4B5563;">
                Se remite el informe epidemiológico de <b>Eficacia Diagnóstica & Hallazgos Críticos</b> consolidado por el Laboratorio Central. A continuación, el resumen de métricas clave:
              </p>

              <table style="width: 100%; margin-bottom: 20px; border-spacing: 6px;">
                <tr>
                  <td style="background-color: #FAF8F5; border: 1px solid #F2E8D8; border-radius: 8px; padding: 10px; text-align: center;">
                    <div style="font-size: 9px; text-transform: uppercase; color: #6B7280; font-weight: bold;">Estudios Procesados</div>
                    <div style="font-size: 18px; font-weight: bold; color: #2D5864;">{kpis['total_estudios_procesados']}</div>
                  </td>
                  <td style="background-color: #FAF8F5; border: 1px solid #F2E8D8; border-radius: 8px; padding: 10px; text-align: center;">
                    <div style="font-size: 9px; text-transform: uppercase; color: #6B7280; font-weight: bold;">Hallazgos Patológicos</div>
                    <div style="font-size: 18px; font-weight: bold; color: #B91C1C;">{kpis['total_con_hallazgos_criticos']}</div>
                  </td>
                  <td style="background-color: #FAF8F5; border: 1px solid #F2E8D8; border-radius: 8px; padding: 10px; text-align: center;">
                    <div style="font-size: 9px; text-transform: uppercase; color: #6B7280; font-weight: bold;">Tasa Positividad</div>
                    <div style="font-size: 18px; font-weight: bold; color: #2D5864;">{kpis['tasa_positividad_porcentaje']}%</div>
                  </td>
                </tr>
                <tr>
                  <td style="background-color: #FAF8F5; border: 1px solid #F2E8D8; border-radius: 8px; padding: 10px; text-align: center;">
                    <div style="font-size: 9px; text-transform: uppercase; color: #6B7280; font-weight: bold;">Concordancia Médica</div>
                    <div style="font-size: 18px; font-weight: bold; color: #047857;">{kpis['tasa_concordancia_diagnostica']}%</div>
                  </td>
                  <td style="background-color: #FAF8F5; border: 1px solid #F2E8D8; border-radius: 8px; padding: 10px; text-align: center;">
                    <div style="font-size: 9px; text-transform: uppercase; color: #6B7280; font-weight: bold;">Fisiológicos Normales</div>
                    <div style="font-size: 18px; font-weight: bold; color: #047857;">{kpis['total_fisiologicos_normales']}</div>
                  </td>
                  <td style="background-color: #FAF8F5; border: 1px solid #F2E8D8; border-radius: 8px; padding: 10px; text-align: center;">
                    <div style="font-size: 9px; text-transform: uppercase; color: #6B7280; font-weight: bold;">Especies Evaluadas</div>
                    <div style="font-size: 18px; font-weight: bold; color: #2D5864;">{kpis['total_especies_auditadas']}</div>
                  </td>
                </tr>
              </table>

              <h3 style="font-size: 13px; color: #2D5864; margin-bottom: 6px;">Distribución Epidemiológica por Especie:</h3>
              <table class="table">
                <thead>
                  <tr>
                    <th>Especie</th>
                    <th style="text-align: center;">Total</th>
                    <th style="text-align: center;">Patológicos</th>
                    <th style="text-align: center;">Normales</th>
                    <th style="text-align: center;">Positividad</th>
                    <th>Patología Predominante</th>
                  </tr>
                </thead>
                <tbody>
                  {filas_esp_html}
                </tbody>
              </table>

              <p style="font-size: 11px; color: #6B7280; margin-top: 20px;">
                Se adjuntan los documentos oficiales en formato <b>PDF</b> (Acta de auditoría médica) y <b>Excel</b> (Libro analítico de datos) según su selección.
              </p>
            </div>

            <div class="footer">
              Patitas & Co. Red Veterinaria & Laboratorio Central de Análisis Clínicos<br/>
              Sistema de Gestión y Trazabilidad Sanitaria · Generado automáticamente
            </div>
          </div>
        </body>
        </html>
        """

        adjuntos: list[tuple[str, bytes, str]] = []
        if incluir_pdf:
            pdf_bytes = self.exportar_pdf_eficacia_diagnostica(datos)
            adjuntos.append(("Reporte_Eficacia_Diagnostica_PatitasCo.pdf", pdf_bytes, "application/pdf"))
        if incluir_excel:
            excel_bytes = self.exportar_excel_eficacia_diagnostica(datos)
            adjuntos.append((
                "Reporte_Eficacia_Diagnostica_PatitasCo.xlsx",
                excel_bytes,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ))

        imagenes_relacionadas: list[tuple[str, bytes, str]] = []
        if RUTA_LOGO.exists():
            try:
                logo_bytes = RUTA_LOGO.read_bytes()
                imagenes_relacionadas.append(("logo_patitas", logo_bytes, "image/png"))
            except Exception as err:
                logger.warning("No se pudo leer el archivo de logo para adjuntar al correo: %s", err)

        servicio_correo = ServicioCorreo()
        enviado = servicio_correo.enviar_reporte(
            destinatario=destinatario,
            asunto=asunto_final,
            cuerpo_texto=cuerpo_texto,
            cuerpo_html=cuerpo_html,
            adjuntos=adjuntos,
            imagenes_relacionadas=imagenes_relacionadas,
        )

        return {
            "exito": enviado,
            "destinatario": destinatario,
            "asunto": asunto_final,
            "adjuntos_incluidos": [a[0] for a in adjuntos],
            "mensaje": (
                f"Reporte de eficacia diagnóstica enviado con éxito a {destinatario}"
                if enviado
                else "No se pudo enviar el correo. Verifique la configuración SMTP en .env."
            ),
        }
