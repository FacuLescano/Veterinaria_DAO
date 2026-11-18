from datetime import datetime
import io
import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.recepcion import obtener_sesion as obtener_sesion_recepcion
from app.models.orden_analisis import Muestra
from app.services.correo_service import ServicioCorreo
from app.services.reportes.base import RUTA_LOGO, fecha_hora_argentina_str

logger = logging.getLogger(__name__)


class ServicioMuestrasRechazadas:
    def __init__(self, db: Session) -> None:
        self.db = db

    def generar_reporte_muestras_rechazadas(
        self,
        fecha_desde: str | None = None,
        fecha_hasta: str | None = None,
        causa_filtro: str | None = None,
        transportista_filtro: str | None = None,
        estado_filtro: str | None = None,
    ) -> dict[str, Any]:
        """Genera las métricas de bioseguridad, causas raíz y confiabilidad de transporte (Reporte 2)."""
        detalles_todos = self._recopilar_detalles_rechazadas()

        # Opciones completas para los filtros disponibles extraídas del universo total
        causas_disponibles = sorted(list(set(d["causa_rechazo"] for d in detalles_todos if d.get("causa_rechazo"))))
        transportistas_disponibles = sorted(list(set(d["transportista"] for d in detalles_todos if d.get("transportista"))))

        detalles = detalles_todos

        # Filtros
        if fecha_desde:
            detalles = [d for d in detalles if d["fecha_evento"][:10] >= fecha_desde[:10]]
        if fecha_hasta:
            detalles = [d for d in detalles if d["fecha_evento"][:10] <= fecha_hasta[:10]]
        if causa_filtro and causa_filtro != "Todas":
            detalles = [
                d for d in detalles
                if d.get("causa_rechazo") and (
                    d["causa_rechazo"].strip().lower() == causa_filtro.strip().lower()
                    or causa_filtro.strip().lower() in d["causa_rechazo"].strip().lower()
                )
            ]
        if transportista_filtro and transportista_filtro != "Todos":
            detalles = [
                d for d in detalles
                if (d.get("transportista") or "").strip().lower() == transportista_filtro.strip().lower()
            ]
        if estado_filtro and estado_filtro != "Todos":
            detalles = [
                d for d in detalles
                if (d.get("estado_muestra") or "").strip().lower() == estado_filtro.strip().lower()
            ]

        auditables = [d for d in detalles if d["estado_muestra"] in {"Rechazada", "Aceptada"}]
        total = len(auditables)
        rechazadas = [d for d in auditables if d["estado_muestra"] == "Rechazada"]
        aceptadas = [d for d in auditables if d["estado_muestra"] == "Aceptada"]
        cant_rechazadas = len(rechazadas)
        cant_aceptadas = len(aceptadas)

        tasa_rechazo = round((cant_rechazadas / total) * 100, 1) if total > 0 else 0.0
        tasa_conformidad = round((cant_aceptadas / total) * 100, 1) if total > 0 else 0.0

        precintos_verificados = [d for d in detalles if d["estado_precinto"] in {"Integro", "Roto", "Ausente"}]
        precintos_integros = sum(1 for d in precintos_verificados if d["estado_precinto"] == "Integro")
        precintos_fallados = len(precintos_verificados) - precintos_integros
        integridad_precintos = round((precintos_integros / len(precintos_verificados)) * 100, 1) if precintos_verificados else 0.0

        temperaturas_medidas = [d for d in detalles if d["temperatura_conforme"] is not None]
        temp_en_rango = sum(1 for d in temperaturas_medidas if d["temperatura_conforme"])
        excursiones = len(temperaturas_medidas) - temp_en_rango
        conformidad_frio = round((temp_en_rango / len(temperaturas_medidas)) * 100, 1) if temperaturas_medidas else 0.0

        # Causas Raíz de Rechazo
        por_causa: dict[str, int] = {}
        for r in rechazadas:
            c = r["causa_rechazo"] or "Falla no especificada"
            por_causa[c] = por_causa.get(c, 0) + 1

        distribucion_causas = []
        for c, count in por_causa.items():
            pct = round((count / cant_rechazadas) * 100, 1) if cant_rechazadas > 0 else 0.0
            distribucion_causas.append({
                "causa": c,
                "cantidad": count,
                "porcentaje": pct,
                "severidad": "Crítica" if "Precinto" in c or "Térmica" in c else "Moderada",
            })
        distribucion_causas.sort(key=lambda x: x["cantidad"], reverse=True)

        # Rendimiento y Confiabilidad por Transportista
        por_transp: dict[str, list[dict[str, Any]]] = {}
        for d in auditables:
            por_transp.setdefault(d["transportista"], []).append(d)

        confiabilidad_transportistas = []
        for tr, items in por_transp.items():
            tot_tr = len(items)
            rech_tr = sum(1 for i in items if i["estado_muestra"] == "Rechazada")
            conf_tr = tot_tr - rech_tr
            pct_conf = round((conf_tr / tot_tr) * 100, 1) if tot_tr > 0 else 100.0
            pct_rech = round((rech_tr / tot_tr) * 100, 1) if tot_tr > 0 else 0.0

            # Falla más frecuente para este transportista
            fallas_tr = [i["causa_rechazo"] for i in items if i["causa_rechazo"]]
            falla_freq = (
                max(set(fallas_tr), key=fallas_tr.count)
                if fallas_tr
                else "Ninguna (100% conforme)"
            )

            confiabilidad_transportistas.append({
                "transportista": tr,
                "total_muestras": tot_tr,
                "muestras_conformes": conf_tr,
                "muestras_rechazadas": rech_tr,
                "tasa_conformidad_porcentaje": pct_conf,
                "tasa_rechazo_porcentaje": pct_rech,
                "falla_frecuente": falla_freq,
                "calificacion": "Excelente" if pct_conf >= 95 else "Aceptable" if pct_conf >= 80 else "Crítico",
            })
        confiabilidad_transportistas.sort(key=lambda x: x["tasa_conformidad_porcentaje"], reverse=True)

        return {
            "fecha_generacion": fecha_hora_argentina_str(),
            "kpis": {
                "total_muestras_auditadas": total,
                "muestras_aceptadas": cant_aceptadas,
                "muestras_rechazadas": cant_rechazadas,
                "tasa_rechazo_global_porcentaje": tasa_rechazo,
                "tasa_conformidad_porcentaje": tasa_conformidad,
                "precintos_integros": precintos_integros,
                "precintos_violados_o_rotos": precintos_fallados,
                "integridad_precintos_porcentaje": integridad_precintos,
                "temperaturas_en_rango": temp_en_rango,
                "excursiones_termicas": excursiones,
                "conformidad_cadena_frio_porcentaje": conformidad_frio,
            },
            "distribucion_causas_rechazo": distribucion_causas,
            "confiabilidad_transportistas": confiabilidad_transportistas,
            "detalles_auditoria": detalles,
            "filtros_disponibles": {
                "causas": ["Todas"] + causas_disponibles,
                "transportistas": ["Todos"] + transportistas_disponibles,
                "estados": ["Todos", "Rechazada", "Aceptada"],
            },
        }

    def _recopilar_detalles_rechazadas(self) -> list[dict[str, Any]]:
        """Recopila muestras e incidencias cruzando con el módulo de recepción y precintos."""
        registros: list[dict[str, Any]] = []

        try:
            recepciones_sesion = next(obtener_sesion_recepcion())
            from app.models.recepcion import Incidencia as IncidenciaM4, VerificacionPrecinto as VerifM4
            incidencias_db = recepciones_sesion.scalars(select(IncidenciaM4)).all()
            verificaciones_db = recepciones_sesion.scalars(select(VerifM4)).all()
            verif_por_envio = {v.envio_id: v for v in verificaciones_db}
            incidencias_por_muestra = {str(i.muestra_id): i for i in incidencias_db if i.muestra_id}

            muestras_db = self.db.scalars(select(Muestra)).all()
            for m in muestras_db:
                orden = m.orden
                pet = orden.consulta.pet if (orden and orden.consulta) else None
                resp = pet.responsible if pet else None
                envio = m.envio

                if envio:
                    incidencia = incidencias_por_muestra.get(str(m.id)) or incidencias_por_muestra.get(m.codigo_etiqueta)
                    verif = verif_por_envio.get(str(envio.id))
                    estados_precinto = {
                        "integro": "Integro", "roto": "Roto", "ausente": "Ausente",
                        "otra_anomalia": "Otra anomalía",
                    }
                    estado_precinto = estados_precinto.get(verif.estado.lower(), "Sin dato") if verif else "Sin dato"

                    temp_salida = None
                    temp_llegada = None
                    if envio.registros_temperatura:
                        temp_salida = envio.registros_temperatura[0].temperatura_medida_c
                        temp_llegada = envio.registros_temperatura[-1].temperatura_medida_c

                    es_rechazada = (
                        m.estado == "rechazada"
                        or estado_precinto in {"Roto", "Ausente", "Otra anomalía"}
                        or (verif is not None and verif.codigo_esperado is not None and verif.codigo_observado != verif.codigo_esperado)
                        or (temp_llegada is not None and not 2.0 <= temp_llegada <= 8.0)
                        or (incidencia is not None and not incidencia.resolucion)
                    )

                    causa = None
                    if estado_precinto == "Roto":
                        causa = "Rotura o Violación de Precinto"
                    elif estado_precinto in {"Codigonocoincide", "Ausente"}:
                        causa = "Código de Precinto No Coincide / Ausente"
                    elif temp_llegada is not None and not 2.0 <= temp_llegada <= 8.0:
                        causa = f"Excursión Térmica ({temp_llegada}°C fuera de 2.0°C a 8.0°C)"
                    elif incidencia:
                        causa = incidencia.tipo

                    registros.append({
                        "muestra_codigo": m.codigo_etiqueta,
                        "paciente_nombre": pet.name if pet else "Sin dato",
                        "especie": pet.species if pet else "Sin dato",
                        "tutor_nombre": resp.full_name if resp else "Sin dato",
                        "tipo_analisis": orden.detalles[0].tipo_analisis.nombre if (orden and orden.detalles) else "Sin dato",
                        "transportista": envio.transportista or "Sin dato",
                        "remito_numero": envio.remito.numero if envio.remito else f"REM-{envio.id:04d}",
                        "conservadora_codigo": envio.conservadora.codigo if envio.conservadora else "Sin dato",
                        "precinto_esperado": verif.codigo_esperado if verif else "Sin dato",
                        "precinto_observado": verif.codigo_observado if verif else "Sin dato",
                        "estado_precinto": estado_precinto if estado_precinto in {"Integro", "Roto", "Ausente"} else "Sin dato",
                        "temperatura_salida_c": temp_salida,
                        "temperatura_llegada_c": temp_llegada,
                        "temperatura_conforme": 2.0 <= temp_llegada <= 8.0 if temp_llegada is not None else None,
                        "rango_admitido": "2.0°C a 8.0°C",
                        "estado_muestra": "Rechazada" if es_rechazada else "Aceptada" if verif or m.estado in {"recibida", "analizada"} else "Sin verificar",
                        "causa_rechazo": causa,
                        "fecha_evento": envio.fecha_despacho.strftime("%Y-%m-%d %H:%M") if envio.fecha_despacho else "Sin dato",
                        "accion_correctiva": "Muestra descartada por protocolo de bioseguridad; re-extracción solicitada" if es_rechazada else "Sin acción correctiva registrada" if not verif else "Muestra recibida conforme",
                    })
        except Exception as err:
            logger.warning("Fallo al consultar base de datos para Reporte 2 (%s)", err)

        return registros

    def exportar_excel_muestras_rechazadas(self, datos: dict[str, Any]) -> bytes:
        """Exporta el Reporte 2 de auditoría sanitaria a un libro Excel (.xlsx)."""
        import openpyxl
        from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
        from openpyxl.utils import get_column_letter

        wb = openpyxl.Workbook()
        ws1 = wb.active
        ws1.title = "Auditoría de Bioseguridad"
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
        fill_rechazo = PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid")
        fill_conforme = PatternFill(start_color="DCFCE7", end_color="DCFCE7", fill_type="solid")

        # Logo
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
        ws1["B1"] = "PATITAS & CO. — AUDITORÍA DE BIOSEGURIDAD Y CONTROL DE TRANSPORTE"
        ws1["B1"].font = Font(name="Calibri", size=14, bold=True, color="2D5864")
        ws1["B1"].alignment = Alignment(horizontal="left", vertical="center")

        ws1.merge_cells("B2:H2")
        ws1["B2"] = f"Reporte 2: Muestras Rechazadas por Fallas en Transporte (Generado: {datos.get('fecha_generacion', '')})"
        ws1["B2"].font = Font(name="Calibri", size=11, italic=True, color="6B7280")

        ws1.row_dimensions[1].height = 24
        ws1.row_dimensions[2].height = 20
        ws1.row_dimensions[3].height = 10

        # Bloque de KPIs
        kpis = datos["kpis"]
        kpi_cards = [
            ("Muestras Auditadas", f"{kpis['total_muestras_auditadas']}"),
            ("Muestras Conformes", f"{kpis['muestras_aceptadas']}"),
            ("Muestras Rechazadas", f"{kpis['muestras_rechazadas']}"),
            ("Tasa de Rechazo", f"{kpis['tasa_rechazo_global_porcentaje']}%"),
            ("Integridad Precintos", f"{kpis['integridad_precintos_porcentaje']}%"),
            ("Cadena de Frío", f"{kpis['conformidad_cadena_frio_porcentaje']}%"),
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

        # Tabla Causas Raíz
        ws1.cell(row=7, column=1, value="Distribución por Causa Raíz de Rechazo").font = Font(name="Calibri", size=12, bold=True, color="2D5864")
        headers_causas = ["Causa de Rechazo", "Casos", "% sobre Rechazos", "Severidad Sanitaria"]
        for col_idx, h in enumerate(headers_causas, start=1):
            cell = ws1.cell(row=8, column=col_idx, value=h)
            cell.font = font_header
            cell.fill = fill_header
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = thin_border

        current_row = 9
        for row_data in datos["distribucion_causas_rechazo"]:
            ws1.cell(row=current_row, column=1, value=row_data["causa"]).border = thin_border
            ws1.cell(row=current_row, column=2, value=row_data["cantidad"]).border = thin_border
            ws1.cell(row=current_row, column=3, value=f"{row_data['porcentaje']}%").border = thin_border
            sev_cell = ws1.cell(row=current_row, column=4, value=row_data["severidad"])
            sev_cell.border = thin_border
            sev_cell.alignment = Alignment(horizontal="center")
            sev_cell.fill = fill_rechazo if row_data["severidad"] == "Crítica" else PatternFill(start_color="FEF3C7", end_color="FEF3C7", fill_type="solid")
            current_row += 1

        # Tabla Confiabilidad Transportistas
        current_row += 2
        ws1.cell(row=current_row, column=1, value="Índice de Confiabilidad por Transportista").font = Font(name="Calibri", size=12, bold=True, color="2D5864")
        current_row += 1
        headers_transp = ["Transportista", "Total Muestras", "Conformes", "Rechazadas", "% Conformidad", "Falla Frecuente"]
        for col_idx, h in enumerate(headers_transp, start=1):
            cell = ws1.cell(row=current_row, column=col_idx, value=h)
            cell.font = font_header
            cell.fill = PatternFill(start_color="5F8E9C", end_color="5F8E9C", fill_type="solid")
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = thin_border

        current_row += 1
        for t_data in datos["confiabilidad_transportistas"]:
            ws1.cell(row=current_row, column=1, value=t_data["transportista"]).border = thin_border
            ws1.cell(row=current_row, column=2, value=t_data["total_muestras"]).border = thin_border
            ws1.cell(row=current_row, column=3, value=t_data["muestras_conformes"]).border = thin_border
            ws1.cell(row=current_row, column=4, value=t_data["muestras_rechazadas"]).border = thin_border
            ws1.cell(row=current_row, column=5, value=f"{t_data['tasa_conformidad_porcentaje']}%").border = thin_border
            ws1.cell(row=current_row, column=6, value=t_data["falla_frecuente"]).border = thin_border
            current_row += 1

        # Hoja 2: Detalle de Muestras e Incidencias
        ws2 = wb.create_sheet(title="Detalle de Muestras")
        ws2.views.sheetView[0].showGridLines = True

        headers_detalles = [
            "Código Muestra", "Paciente", "Especie", "Tutor", "Tipo Análisis",
            "Transportista", "Remito", "Precinto Obs.", "Estado Precinto",
            "T° Llegada", "Estado Muestra", "Causa de Rechazo", "Acción Correctiva"
        ]

        for col_idx, h in enumerate(headers_detalles, start=1):
            cell = ws2.cell(row=1, column=col_idx, value=h)
            cell.font = font_header
            cell.fill = fill_header
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = thin_border

        for r_idx, d in enumerate(datos["detalles_auditoria"], start=2):
            ws2.cell(row=r_idx, column=1, value=d["muestra_codigo"]).border = thin_border
            ws2.cell(row=r_idx, column=2, value=d["paciente_nombre"]).border = thin_border
            ws2.cell(row=r_idx, column=3, value=d["especie"]).border = thin_border
            ws2.cell(row=r_idx, column=4, value=d["tutor_nombre"]).border = thin_border
            ws2.cell(row=r_idx, column=5, value=d["tipo_analisis"]).border = thin_border
            ws2.cell(row=r_idx, column=6, value=d["transportista"]).border = thin_border
            ws2.cell(row=r_idx, column=7, value=d["remito_numero"]).border = thin_border
            ws2.cell(row=r_idx, column=8, value=d["precinto_observado"]).border = thin_border
            ws2.cell(row=r_idx, column=9, value=d["estado_precinto"]).border = thin_border
            ws2.cell(row=r_idx, column=10, value=f"{d['temperatura_llegada_c']}°C").border = thin_border

            est_cell = ws2.cell(row=r_idx, column=11, value=d["estado_muestra"])
            est_cell.border = thin_border
            est_cell.alignment = Alignment(horizontal="center")
            est_cell.fill = fill_rechazo if d["estado_muestra"] == "Rechazada" else fill_conforme

            ws2.cell(row=r_idx, column=12, value=d["causa_rechazo"] or "-").border = thin_border
            ws2.cell(row=r_idx, column=13, value=d["accion_correctiva"]).border = thin_border

        for sheet in (ws1, ws2):
            for col in sheet.columns:
                max_len = max(len(str(cell.value or "")) for cell in col)
                col_letter = get_column_letter(col[0].column)
                sheet.column_dimensions[col_letter].width = max(max_len + 3, 12)

        output = io.BytesIO()
        wb.save(output)
        return output.getvalue()

    def exportar_pdf_muestras_rechazadas(self, datos: dict[str, Any]) -> bytes:
        """Exporta el Reporte 2 en formato PDF oficial apaisado."""
        from reportlab.lib.pagesizes import letter, landscape
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(letter),
            leftMargin=28,
            rightMargin=28,
            topMargin=28,
            bottomMargin=28,
        )

        styles = getSampleStyleSheet()
        style_title = ParagraphStyle(
            "TitleStyle2",
            parent=styles["Heading1"],
            fontSize=15,
            leading=18,
            textColor=colors.HexColor("#2D5864"),
            spaceAfter=2,
        )
        style_subtitle = ParagraphStyle(
            "SubTitleStyle2",
            parent=styles["Normal"],
            fontSize=9,
            leading=11,
            textColor=colors.HexColor("#6B7280"),
            spaceAfter=10,
        )
        style_cell = ParagraphStyle("Cell2", parent=styles["Normal"], fontSize=8, leading=10)
        style_cell_bold = ParagraphStyle("CellBold2", parent=styles["Normal"], fontSize=8, leading=10, fontName="Helvetica-Bold")
        style_cell_header = ParagraphStyle("CellHeader2", parent=styles["Normal"], fontSize=8, leading=10, fontName="Helvetica-Bold", textColor=colors.white)

        elements = []

        if RUTA_LOGO.exists():
            try:
                from reportlab.platypus import Image as RLImage
                logo_rl = RLImage(str(RUTA_LOGO), width=44, height=44)
                header_table = Table(
                    [[
                        logo_rl,
                        [
                            Paragraph("PATITAS & CO. — AUDITORÍA DE BIOSEGURIDAD Y CONTROL DE TRANSPORTE", style_title),
                            Paragraph(f"Reporte 2: Muestras Rechazadas por Fallas en Transporte y Cadena de Custodia · Generado el {datos.get('fecha_generacion', '')}", style_subtitle),
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
                elements.append(Paragraph("PATITAS & CO. — AUDITORÍA DE BIOSEGURIDAD Y CONTROL DE TRANSPORTE", style_title))
                elements.append(Paragraph(f"Reporte 2: Muestras Rechazadas por Fallas en Transporte · Generado el {datos.get('fecha_generacion', '')}", style_subtitle))
        else:
            elements.append(Paragraph("PATITAS & CO. — AUDITORÍA DE BIOSEGURIDAD Y CONTROL DE TRANSPORTE", style_title))
            elements.append(Paragraph(f"Reporte 2: Muestras Rechazadas por Fallas en Transporte · Generado el {datos.get('fecha_generacion', '')}", style_subtitle))

        # Tarjetas KPIs
        kpis = datos["kpis"]
        kpi_data = [
            ["Muestras Auditadas", "Muestras Conformes", "Muestras Rechazadas", "Tasa de Rechazo", "Integridad Precintos", "Cadena de Frío"],
            [
                str(kpis["total_muestras_auditadas"]),
                str(kpis["muestras_aceptadas"]),
                str(kpis["muestras_rechazadas"]),
                f"{kpis['tasa_rechazo_global_porcentaje']}%",
                f"{kpis['integridad_precintos_porcentaje']}%",
                f"{kpis['conformidad_cadena_frio_porcentaje']}%",
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
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#E7E2DA")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E7E2DA")),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        elements.append(t_kpi)
        elements.append(Spacer(1, 12))

        # Tabla Causas de Rechazo
        elements.append(Paragraph("<b>Causas Raíz de Rechazo y Severidad Sanitaria</b>", ParagraphStyle("H2_2", parent=styles["Heading2"], fontSize=10, textColor=colors.HexColor("#2D5864"))))
        causas_data = [
            [
                Paragraph("Causa de Rechazo", style_cell_header),
                Paragraph("Casos", style_cell_header),
                Paragraph("% s/ Rechazos", style_cell_header),
                Paragraph("Severidad Sanitaria", style_cell_header),
            ]
        ]
        for row in datos["distribucion_causas_rechazo"]:
            causas_data.append([
                Paragraph(row["causa"], style_cell_bold),
                Paragraph(str(row["cantidad"]), style_cell),
                Paragraph(f"{row['porcentaje']}%", style_cell),
                Paragraph(row["severidad"], ParagraphStyle("Sev", parent=style_cell_bold, textColor=colors.HexColor("#991B1B" if row["severidad"] == "Crítica" else "#D97706"))),
            ])

        t_causas = Table(causas_data, colWidths=[330, 80, 120, 200])
        t_causas.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2D5864")),
            ("ALIGN", (1, 0), (2, -1), "CENTER"),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#9CA3AF")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        elements.append(t_causas)
        elements.append(Spacer(1, 12))

        # Tabla Muestras Rechazadas Detalle
        elements.append(Paragraph("<b>Registro de Muestras Auditadas (Rechazos y Casos Conformes)</b>", ParagraphStyle("H2_3", parent=styles["Heading2"], fontSize=10, textColor=colors.HexColor("#2D5864"))))
        det_data = [
            [
                Paragraph("Muestra", style_cell_header),
                Paragraph("Paciente / Tutor", style_cell_header),
                Paragraph("Transportista", style_cell_header),
                Paragraph("Precinto", style_cell_header),
                Paragraph("T° Llegada", style_cell_header),
                Paragraph("Estado", style_cell_header),
                Paragraph("Causa de Rechazo / Acción Correctiva", style_cell_header),
            ]
        ]
        for d in datos["detalles_auditoria"][:10]:
            es_rech = d["estado_muestra"] == "Rechazada"
            det_data.append([
                Paragraph(d["muestra_codigo"], style_cell_bold),
                Paragraph(f"{d['paciente_nombre']} ({d['tutor_nombre']})", style_cell),
                Paragraph(d["transportista"], style_cell),
                Paragraph(f"{d['estado_precinto']}", style_cell),
                Paragraph(f"{d['temperatura_llegada_c']}°C", style_cell),
                Paragraph(d["estado_muestra"], ParagraphStyle("StR", parent=style_cell_bold, textColor=colors.HexColor("#991B1B" if es_rech else "#166534"))),
                Paragraph(d["causa_rechazo"] or d["accion_correctiva"], style_cell),
            ])

        t_det = Table(det_data, colWidths=[65, 140, 130, 65, 55, 65, 210])
        t_det.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#5F8E9C")),
            ("ALIGN", (3, 0), (5, -1), "CENTER"),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#9CA3AF")),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        elements.append(t_det)

        doc.build(elements)
        return buffer.getvalue()

    def enviar_reporte_rechazadas_email(
        self,
        destinatario: str,
        asunto: str | None = None,
        incluir_pdf: bool = True,
        incluir_excel: bool = True,
        datos: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Envía el Reporte 2 por correo electrónico con KPIs de rechazos, logo CID y adjuntos."""
        if datos is None:
            datos = self.generar_reporte_muestras_rechazadas()

        asunto_final = asunto or f"Auditoría Sanitaria: Muestras Rechazadas en Transporte — Patitas & Co. ({datos.get('fecha_generacion', '')})"
        kpis = datos["kpis"]

        cuerpo_texto = f"""
PATITAS & CO. — AUDITORÍA DE BIOSEGURIDAD Y CONTROL DE TRANSPORTE
REPORTE 2: MUESTRAS RECHAZADAS POR FALLAS EN TRANSPORTE

Resumen de Bioseguridad:
- Total Muestras Auditadas: {kpis['total_muestras_auditadas']}
- Muestras Conformes (Aceptadas): {kpis['muestras_aceptadas']}
- Muestras Rechazadas: {kpis['muestras_rechazadas']}
- Tasa de Rechazo Global: {kpis['tasa_rechazo_global_porcentaje']}%
- Integridad de Precintos: {kpis['integridad_precintos_porcentaje']}%
- Conformidad de Cadena de Frío: {kpis['conformidad_cadena_frio_porcentaje']}%

Este reporte se emite conforme a la normativa sanitaria SENASA Res. N° 412/2026.
        """.strip()

        filas_causas_html = "".join([
            f"""
            <tr style="border-bottom: 1px solid #E5E7EB;">
                <td style="padding: 8px; font-weight: 600; color: #1F2937;">{row['causa']}</td>
                <td style="padding: 8px; text-align: center; font-weight: bold; color: #DC2626;">{row['cantidad']}</td>
                <td style="padding: 8px; text-align: center;">{row['porcentaje']}%</td>
                <td style="padding: 8px; text-align: center; font-weight: bold; color: {'#991B1B' if row['severidad'] == 'Crítica' else '#D97706'};">{row['severidad']}</td>
            </tr>
            """
            for row in datos["distribucion_causas_rechazo"]
        ])

        cuerpo_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; color: #1F2937; line-height: 1.5; }}
                .container {{ max-width: 650px; margin: 0 auto; padding: 20px; border: 1px solid #E5E7EB; border-radius: 12px; }}
                .header {{ background-color: #2D5864; color: white; padding: 18px 20px; border-radius: 8px; }}
                .kpi-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin: 20px 0; }}
                .kpi-card {{ background-color: #FAF6EF; border: 1px solid #F2E8D8; border-radius: 8px; padding: 12px; text-align: center; }}
                .kpi-val {{ font-size: 20px; font-weight: bold; color: #2D5864; }}
                .kpi-lbl {{ font-size: 11px; color: #6B7280; text-transform: uppercase; margin-top: 4px; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 15px; font-size: 12px; }}
                th {{ background-color: #5F8E9C; color: white; padding: 8px; text-align: center; }}
                .footer {{ margin-top: 25px; padding-top: 15px; border-top: 1px solid #E5E7EB; font-size: 11px; color: #9CA3AF; text-align: center; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <table style="width: 100%; border: none; margin: 0; padding: 0; background-color: transparent;">
                        <tr>
                            <td style="width: 55px; vertical-align: middle; border: none; padding: 0;">
                                <img src="cid:logo_patitas" alt="Logo Patitas & Co." width="46" height="46" style="vertical-align: middle; border-radius: 8px; background: white; padding: 3px; display: block;" />
                            </td>
                            <td style="vertical-align: middle; border: none; padding-left: 14px; text-align: left;">
                                <h2 style="margin: 0; font-size: 18px; color: white; line-height: 1.2;">PATITAS & CO. — BIOSEGURIDAD</h2>
                                <p style="margin: 3px 0 0; font-size: 12px; color: #E0E7FF; opacity: 0.95;">Auditoría de Muestras Rechazadas en Transporte Biológico</p>
                            </td>
                        </tr>
                    </table>
                </div>

                <div class="kpi-grid">
                    <div class="kpi-card">
                        <div class="kpi-val" style="color: {'#DC2626' if kpis['tasa_rechazo_global_porcentaje'] > 10 else '#2D5864'};">{kpis['tasa_rechazo_global_porcentaje']}%</div>
                        <div class="kpi-lbl">Tasa de Rechazo</div>
                    </div>
                    <div class="kpi-card">
                        <div class="kpi-val">{kpis['integridad_precintos_porcentaje']}%</div>
                        <div class="kpi-lbl">Integridad Precintos</div>
                    </div>
                    <div class="kpi-card">
                        <div class="kpi-val">{kpis['conformidad_cadena_frio_porcentaje']}%</div>
                        <div class="kpi-lbl">Cadena de Frío</div>
                    </div>
                </div>

                <h3 style="font-size: 14px; color: #2D5864; margin-top: 20px;">Causas Raíz de Rechazo Sanitario</h3>
                <table>
                    <thead>
                        <tr>
                            <th style="text-align: left;">Causa de Rechazo</th>
                            <th>Casos</th>
                            <th>% s/ Rechazos</th>
                            <th>Severidad</th>
                        </tr>
                    </thead>
                    <tbody>
                        {filas_causas_html}
                    </tbody>
                </table>

                <p style="font-size: 12px; color: #6B7280; margin-top: 20px;">
                    Adjunto encontrará el informe técnico en PDF y el libro Excel de auditoría con la trazabilidad completa de cada tubo rechazado.
                </p>

                <div class="footer">
                    Patitas & Co. Red Veterinaria & Laboratorio Central · Res. SENASA N° 412/2026 · Córdoba, Argentina
                </div>
            </div>
        </body>
        </html>
        """

        adjuntos: list[tuple[str, bytes, str]] = []
        if incluir_pdf:
            pdf_bytes = self.exportar_pdf_muestras_rechazadas(datos)
            adjuntos.append(("Reporte_Muestras_Rechazadas_PatitasCo.pdf", pdf_bytes, "application/pdf"))
        if incluir_excel:
            excel_bytes = self.exportar_excel_muestras_rechazadas(datos)
            adjuntos.append((
                "Reporte_Muestras_Rechazadas_PatitasCo.xlsx",
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
                f"Reporte de muestras rechazadas enviado con éxito a {destinatario}"
                if enviado
                else "No se pudo enviar el correo. Verifique la configuración SMTP en .env."
            ),
        }

