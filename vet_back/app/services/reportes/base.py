from datetime import datetime, timezone, timedelta
from pathlib import Path
import logging
from typing import Any

logger = logging.getLogger(__name__)

# Zona horaria oficial de Argentina (UTC-3)
TZ_ARGENTINA = timezone(timedelta(hours=-3))


def ahora_argentina() -> datetime:
    return datetime.now(TZ_ARGENTINA)


def fecha_hora_argentina_str(fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    return ahora_argentina().strftime(fmt)


# Resolución del logotipo oficial del sistema
DIRECTORIO_APP = Path(__file__).resolve().parent.parent.parent
RUTA_LOGO = DIRECTORIO_APP / "static" / "logo.png"
if not RUTA_LOGO.exists():
    RUTA_LOGO = (
        DIRECTORIO_APP.parent.parent
        / "vet_front"
        / "public"
        / "assets"
        / "aistudio"
        / "Gemini_Generated_Image_o95dgio95dgio95d-removebg-preview_cbe90b76.png"
    )


def exportar_reporte_excel(titulo: str, datos: dict[str, Any], secciones: list[tuple[str, str]]) -> bytes:
    """Exporta los indicadores y desgloses vigentes de un reporte."""
    import io
    import openpyxl
    from openpyxl.styles import Font, PatternFill

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Resumen"
    ws.append([titulo])
    ws["A1"].font = Font(bold=True, size=16, color="2D5864")
    ws.append(["Indicador", "Valor"])
    for cell in ws[2]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="2D5864")
    for nombre, valor in datos.get("kpis", {}).items():
        ws.append([nombre.replace("_", " ").capitalize(), "Sin información suficiente" if valor is None else valor])
    for etiqueta, clave in secciones:
        filas = datos.get(clave, [])
        if not isinstance(filas, list) or not filas:
            continue
        ws.append([])
        ws.append([etiqueta])
        encabezados = list(filas[0].keys())
        ws.append(encabezados)
        for fila in filas:
            ws.append([fila.get(campo) for campo in encabezados])
    ws.freeze_panes = "A3"
    for columna in ws.columns:
        letra = columna[0].column_letter
        ws.column_dimensions[letra].width = min(42, max(14, max(len(str(c.value or "")) for c in columna) + 2))
    salida = io.BytesIO()
    wb.save(salida)
    return salida.getvalue()


def exportar_reporte_pdf(titulo: str, datos: dict[str, Any], secciones: list[tuple[str, str]]) -> bytes:
    """Genera el resumen PDF con los mismos KPI y desgloses del reporte."""
    import io
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    salida = io.BytesIO()
    doc = SimpleDocTemplate(salida, pagesize=landscape(A4), rightMargin=32, leftMargin=32, topMargin=30, bottomMargin=30)
    estilos = getSampleStyleSheet()
    contenido: list[Any] = [Paragraph(titulo, estilos["Title"]), Spacer(1, 12)]
    kpis = [["Indicador", "Valor"]]
    kpis.extend([[nombre.replace("_", " ").capitalize(), "Sin información suficiente" if valor is None else str(valor)] for nombre, valor in datos.get("kpis", {}).items()])
    tabla = Table(kpis, repeatRows=1, hAlign="LEFT")
    tabla.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2D5864")), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white), ("GRID", (0, 0), (-1, -1), .4, colors.HexColor("#D1D5DB")), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    contenido.append(tabla)
    for etiqueta, clave in secciones:
        filas = datos.get(clave, [])
        if not isinstance(filas, list) or not filas:
            continue
        contenido.extend([Spacer(1, 12), Paragraph(etiqueta, estilos["Heading2"])])
        cabeceras = list(filas[0].keys())
        filas_pdf = [[str(c).replace("_", " ") for c in cabeceras]]
        filas_pdf.extend([[str(f.get(campo, "")) for campo in cabeceras] for f in filas[:40]])
        tabla = Table(filas_pdf, repeatRows=1, hAlign="LEFT")
        tabla.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2D5864")), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white), ("GRID", (0, 0), (-1, -1), .35, colors.HexColor("#D1D5DB")), ("FONTSIZE", (0, 0), (-1, -1), 7), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
        contenido.append(tabla)
    doc.build(contenido)
    return salida.getvalue()


def enviar_reporte_email(destinatario: str, asunto: str | None, incluir_pdf: bool, incluir_excel: bool, datos: dict[str, Any], titulo: str, exportar_pdf_fn: Any, exportar_excel_fn: Any) -> dict[str, Any]:
    from app.services.correo_service import ServicioCorreo

    adjuntos = []
    if incluir_pdf:
        adjuntos.append((f"{titulo}.pdf", exportar_pdf_fn(datos), "application/pdf"))
    if incluir_excel:
        adjuntos.append((f"{titulo}.xlsx", exportar_excel_fn(datos), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"))
    lineas = [titulo.replace("_", " "), "", "Indicadores del período:"]
    lineas.extend(f"- {nombre.replace('_', ' ').capitalize()}: {valor if valor is not None else 'Sin información suficiente'}" for nombre, valor in datos.get("kpis", {}).items())
    asunto_final = asunto or titulo.replace("_", " ")
    exito = ServicioCorreo().enviar_reporte(destinatario, asunto_final, "\n".join(lineas), adjuntos=adjuntos)
    return {"exito": exito, "destinatario": destinatario, "asunto": asunto_final, "adjuntos_incluidos": [a[0] for a in adjuntos], "mensaje": f"Reporte enviado con éxito a {destinatario}" if exito else "No se pudo enviar el correo. Verifique la configuración SMTP en .env."}

