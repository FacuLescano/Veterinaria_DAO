"""Tests unitarios y de integración para el Reporte 1: Tiempos de Tránsito y SLA."""

import pytest
from test.conftest import TestingSessionLocal
from app.services.reportes_service import ReportesService, MATRIZ_SLA


@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_generar_reporte_tiempos_sla(db_session):
    service = ReportesService(db_session)
    reporte = service.generar_reporte_tiempos_sla()

    assert "kpis" in reporte
    assert "sla_por_tipo_analisis" in reporte
    assert "rendimiento_transportistas" in reporte
    assert "detalles_muestras" in reporte

    kpis = reporte["kpis"]
    assert kpis["total_muestras_analizadas"] >= 6
    assert kpis["tiempo_promedio_transito_horas"] > 0
    assert kpis["tiempo_promedio_total_horas"] > 0
    assert 0 <= kpis["tasa_cumplimiento_sla_porcentaje"] <= 100

    # Verificar cálculo de SLA por tipo de análisis
    for row in reporte["sla_por_tipo_analisis"]:
        assert row["tipo_analisis"] in MATRIZ_SLA or row["tipo_analisis"] is not None
        assert row["sla_objetivo_horas"] > 0
        assert 0 <= row["cumplimiento_porcentaje"] <= 100
        assert row["estado_sla"] in {"Cumplido", "En riesgo", "Excedido"}


def test_filtros_reporte_tiempos_sla(db_session):
    service = ReportesService(db_session)
    # Filtro por prioridad
    reporte_urgente = service.generar_reporte_tiempos_sla(prioridad_filtro="Urgente")
    for d in reporte_urgente["detalles_muestras"]:
        assert d["prioridad"] == "Urgente"

    # Filtro por tipo de análisis
    reporte_hemo = service.generar_reporte_tiempos_sla(tipo_analisis_filtro="Hemograma Completo")
    for d in reporte_hemo["detalles_muestras"]:
        assert d["tipo_analisis"] == "Hemograma Completo"


def test_exportar_excel(db_session):
    service = ReportesService(db_session)
    datos = service.generar_reporte_tiempos_sla()
    excel_bytes = service.exportar_excel(datos)

    assert isinstance(excel_bytes, bytes)
    assert len(excel_bytes) > 2000  # Archivo binario xlsx generado con contenido


def test_exportar_pdf(db_session):
    service = ReportesService(db_session)
    datos = service.generar_reporte_tiempos_sla()
    pdf_bytes = service.exportar_pdf(datos)

    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes.startswith(b"%PDF")
    assert len(pdf_bytes) > 1000


def test_endpoint_reporte_json(client):
    response = client.get("/api/v1/reportes/tiempos-sla")
    assert response.status_code == 200
    data = response.json()
    assert "kpis" in data
    assert "sla_por_tipo_analisis" in data
    assert "detalles_muestras" in data


def test_endpoint_descargar_excel(client):
    response = client.get("/api/v1/reportes/tiempos-sla/excel")
    assert response.status_code == 200
    assert "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" in response.headers["content-type"]
    assert len(response.content) > 2000


def test_endpoint_descargar_pdf(client):
    response = client.get("/api/v1/reportes/tiempos-sla/pdf")
    assert response.status_code == 200
    assert "application/pdf" in response.headers["content-type"]
    assert response.content.startswith(b"%PDF")


# ==============================================================================
# TESTS REPORTE 2: Muestras Rechazadas por Fallas en Transporte y Bioseguridad
# ==============================================================================

def test_generar_reporte_muestras_rechazadas(db_session):
    service = ReportesService(db_session)
    reporte = service.generar_reporte_muestras_rechazadas()

    assert "kpis" in reporte
    assert "distribucion_causas_rechazo" in reporte
    assert "confiabilidad_transportistas" in reporte
    assert "detalles_auditoria" in reporte

    kpis = reporte["kpis"]
    assert kpis["total_muestras_auditadas"] >= 8
    assert kpis["muestras_rechazadas"] > 0
    assert kpis["muestras_aceptadas"] > 0
    assert 0 <= kpis["tasa_rechazo_global_porcentaje"] <= 100
    assert 0 <= kpis["integridad_precintos_porcentaje"] <= 100
    assert 0 <= kpis["conformidad_cadena_frio_porcentaje"] <= 100

    # Verificar causas de rechazo
    assert len(reporte["distribucion_causas_rechazo"]) > 0
    for causa in reporte["distribucion_causas_rechazo"]:
        assert causa["cantidad"] > 0
        assert 0 <= causa["porcentaje"] <= 100
        assert causa["severidad"] in {"Crítica", "Moderada"}


def test_filtros_muestras_rechazadas(db_session):
    service = ReportesService(db_session)
    # Filtro por estado
    solo_rechazadas = service.generar_reporte_muestras_rechazadas(estado_filtro="Rechazada")
    for d in solo_rechazadas["detalles_auditoria"]:
        assert d["estado_muestra"] == "Rechazada"

    solo_aceptadas = service.generar_reporte_muestras_rechazadas(estado_filtro="Aceptada")
    for d in solo_aceptadas["detalles_auditoria"]:
        assert d["estado_muestra"] == "Aceptada"


def test_exportar_excel_muestras_rechazadas(db_session):
    service = ReportesService(db_session)
    datos = service.generar_reporte_muestras_rechazadas()
    excel_bytes = service.exportar_excel_muestras_rechazadas(datos)

    assert isinstance(excel_bytes, bytes)
    assert len(excel_bytes) > 2000


def test_exportar_pdf_muestras_rechazadas(db_session):
    service = ReportesService(db_session)
    datos = service.generar_reporte_muestras_rechazadas()
    pdf_bytes = service.exportar_pdf_muestras_rechazadas(datos)

    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes.startswith(b"%PDF")
    assert len(pdf_bytes) > 1000


def test_endpoint_muestras_rechazadas_json(client):
    response = client.get("/api/v1/reportes/muestras-rechazadas")
    assert response.status_code == 200
    data = response.json()
    assert "kpis" in data
    assert "distribucion_causas_rechazo" in data
    assert "confiabilidad_transportistas" in data
    assert "detalles_auditoria" in data
    assert len(data["filtros_disponibles"]["causas"]) >= 4

    # Probar filtrado por causa usando tanto 'causa' como 'causa_rechazo'
    res_causa = client.get("/api/v1/reportes/muestras-rechazadas?causa=Excursi%C3%B3n+T%C3%A9rmica")
    assert res_causa.status_code == 200
    data_causa = res_causa.json()
    assert len(data_causa["detalles_auditoria"]) >= 1
    for d in data_causa["detalles_auditoria"]:
        assert "Excursión Térmica" in d["causa_rechazo"]
    # Los filtros disponibles no deben vaciarse al filtrar
    assert len(data_causa["filtros_disponibles"]["causas"]) >= 4

    res_alias = client.get("/api/v1/reportes/muestras-rechazadas?causa_rechazo=Precinto")
    assert res_alias.status_code == 200
    data_alias = res_alias.json()
    assert len(data_alias["detalles_auditoria"]) >= 1
    for d in data_alias["detalles_auditoria"]:
        assert "Precinto" in d["causa_rechazo"]


def test_endpoint_muestras_rechazadas_excel(client):
    response = client.get("/api/v1/reportes/muestras-rechazadas/excel")
    assert response.status_code == 200
    assert "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" in response.headers["content-type"]
    assert len(response.content) > 2000


def test_endpoint_muestras_rechazadas_pdf(client):
    response = client.get("/api/v1/reportes/muestras-rechazadas/pdf")
    assert response.status_code == 200
    assert "application/pdf" in response.headers["content-type"]
    assert response.content.startswith(b"%PDF")

