"""Tests unitarios y de integración para el Reporte 1: Tiempos de Tránsito y SLA."""

from datetime import datetime
from types import SimpleNamespace

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
    assert kpis["total_muestras_analizadas"] == 0
    assert kpis["tiempo_promedio_transito_horas"] == 0
    assert kpis["tiempo_promedio_total_horas"] == 0
    assert reporte["detalles_muestras"] == []
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


def test_fecha_de_resultado_heredada_anterior_al_ingreso_usa_fecha_real_de_registro(db_session):
    service = ReportesService(db_session)._servicio_tiempos
    ingreso = datetime(2026, 11, 12, 22, 43)
    fecha_registro = datetime(2026, 11, 13, 1, 0)
    resultado = SimpleNamespace(
        fecha_recepcion=datetime(2026, 1, 1),
        creado_en=fecha_registro,
    )

    assert service._fecha_resultado_valida(resultado, ingreso) == fecha_registro

    resultado.creado_en = datetime(2026, 11, 12, 20, 0)
    assert service._fecha_resultado_valida(resultado, ingreso) is None


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
    assert kpis["total_muestras_auditadas"] == 0
    assert kpis["muestras_rechazadas"] == 0
    assert kpis["muestras_aceptadas"] == 0
    assert 0 <= kpis["tasa_rechazo_global_porcentaje"] <= 100
    assert 0 <= kpis["integridad_precintos_porcentaje"] <= 100
    assert 0 <= kpis["conformidad_cadena_frio_porcentaje"] <= 100

    # Verificar causas de rechazo
    assert reporte["detalles_auditoria"] == []
    assert reporte["distribucion_causas_rechazo"] == []
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
    assert data["filtros_disponibles"]["causas"] == ["Todas"]

    # Probar filtrado por causa usando tanto 'causa' como 'causa_rechazo'
    res_causa = client.get("/api/v1/reportes/muestras-rechazadas?causa=Excursi%C3%B3n+T%C3%A9rmica")
    assert res_causa.status_code == 200
    data_causa = res_causa.json()
    assert data_causa["detalles_auditoria"] == []
    for d in data_causa["detalles_auditoria"]:
        assert "Excursión Térmica" in d["causa_rechazo"]
    # Los filtros disponibles no deben vaciarse al filtrar
    assert data_causa["filtros_disponibles"]["causas"] == ["Todas"]

    res_alias = client.get("/api/v1/reportes/muestras-rechazadas?causa_rechazo=Precinto")
    assert res_alias.status_code == 200
    data_alias = res_alias.json()
    assert data_alias["detalles_auditoria"] == []
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


# ==============================================================================
# TESTS REPORTE 3: Rendimiento Clínico y Tasa de Derivación Médica
# ==============================================================================

def test_generar_reporte_rendimiento_clinico(db_session):
    service = ReportesService(db_session)
    reporte = service.generar_reporte_rendimiento_clinico()

    assert "kpis" in reporte
    assert "rendimiento_veterinarios" in reporte
    assert "top_estudios_prescriptos" in reporte
    assert "distribucion_estados_turno" in reporte
    assert "detalles_consultas" in reporte
    assert "filtros_disponibles" in reporte

    kpis = reporte["kpis"]
    assert kpis["total_turnos_agendados"] == 0
    assert kpis["turnos_atendidos"] == 0
    assert 0 <= kpis["tasa_ausentismo_porcentaje"] <= 100
    assert 0 <= kpis["tasa_derivacion_global_porcentaje"] <= 100
    assert kpis["total_ordenes_laboratorio"] == 0
    assert kpis["total_estudios_solicitados"] == 0

    # Verificar veterinarios
    assert reporte["rendimiento_veterinarios"] == []
    for v in reporte["rendimiento_veterinarios"]:
        assert v["turnos_asignados"] > 0
        assert 0 <= v["tasa_asistencia_porcentaje"] <= 100
        assert 0 <= v["tasa_derivacion_porcentaje"] <= 100
        assert v["perfil_prescriptivo"] in {
            "Alta Derivación (>60%)",
            "Derivación Moderada (30-60%)",
            "Clínico Conservador (<30%)",
        }


def test_filtros_rendimiento_clinico(db_session):
    service = ReportesService(db_session)

    # Filtro por médico veterinario
    rep_vet = service.generar_reporte_rendimiento_clinico(veterinario_filtro="Sofía Martínez")
    for d in rep_vet["detalles_consultas"]:
        assert "Sofía Martínez" in d["veterinario_nombre"]

    # Filtro por derivación
    rep_deriv = service.generar_reporte_rendimiento_clinico(derivacion_filtro="Con Derivación")
    for d in rep_deriv["detalles_consultas"]:
        assert d["derivo_laboratorio"] is True

    rep_sin_deriv = service.generar_reporte_rendimiento_clinico(derivacion_filtro="Sin Derivación")
    for d in rep_sin_deriv["detalles_consultas"]:
        assert d["derivo_laboratorio"] is False


def test_exportar_excel_rendimiento_clinico(db_session):
    service = ReportesService(db_session)
    datos = service.generar_reporte_rendimiento_clinico()
    excel_bytes = service.exportar_excel_rendimiento_clinico(datos)

    assert isinstance(excel_bytes, bytes)
    assert len(excel_bytes) > 2000


def test_exportar_pdf_rendimiento_clinico(db_session):
    service = ReportesService(db_session)
    datos = service.generar_reporte_rendimiento_clinico()
    pdf_bytes = service.exportar_pdf_rendimiento_clinico(datos)

    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes.startswith(b"%PDF")
    assert len(pdf_bytes) > 1000


def test_endpoint_rendimiento_clinico_json(client):
    response = client.get("/api/v1/reportes/rendimiento-clinico")
    assert response.status_code == 200
    data = response.json()
    assert "kpis" in data
    assert "rendimiento_veterinarios" in data
    assert "top_estudios_prescriptos" in data
    assert "detalles_consultas" in data
    assert data["filtros_disponibles"]["veterinarios"] == ["Todos"]

    # Probar filtrado por veterinario
    res_vet = client.get("/api/v1/reportes/rendimiento-clinico?veterinario=Lucas+Ferrara")
    assert res_vet.status_code == 200
    data_vet = res_vet.json()
    assert data_vet["detalles_consultas"] == []
    for d in data_vet["detalles_consultas"]:
        assert "Lucas Ferrara" in d["veterinario_nombre"]


def test_endpoint_rendimiento_clinico_excel(client):
    response = client.get("/api/v1/reportes/rendimiento-clinico/excel")
    assert response.status_code == 200
    assert "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" in response.headers["content-type"]
    assert len(response.content) > 2000


def test_endpoint_rendimiento_clinico_pdf(client):
    response = client.get("/api/v1/reportes/rendimiento-clinico/pdf")
    assert response.status_code == 200
    assert "application/pdf" in response.headers["content-type"]
    assert response.content.startswith(b"%PDF")


# ==========================================
# Tests para Reporte 4: Eficacia Diagnóstica & Hallazgos Críticos
# ==========================================


def test_generar_reporte_eficacia_diagnostica(db_session):
    service = ReportesService(db_session)
    reporte = service.generar_reporte_eficacia_diagnostica()

    assert "kpis" in reporte
    assert "desglose_por_especie" in reporte
    assert "desglose_por_grupo_etario" in reporte
    assert "top_analitos_criticos" in reporte
    assert "distribucion_severidad" in reporte
    assert "detalles_diagnosticos" in reporte

    kpis = reporte["kpis"]
    assert kpis["total_estudios_procesados"] == 0
    assert kpis["total_con_hallazgos_criticos"] == 0
    assert kpis["total_fisiologicos_normales"] == 0
    assert 0 <= kpis["tasa_positividad_porcentaje"] <= 100
    assert kpis["total_especies_auditadas"] == 0
    assert kpis["tasa_concordancia_diagnostica"] is None


def test_filtros_reporte_eficacia_diagnostica(db_session):
    service = ReportesService(db_session)

    # Filtrar por especie Canino
    rep_can = service.generar_reporte_eficacia_diagnostica(especie_filtro="Canino")
    assert rep_can["detalles_diagnosticos"] == []
    for d in rep_can["detalles_diagnosticos"]:
        assert d["especie"] == "Canino"

    # Filtrar por especie Felino
    rep_fel = service.generar_reporte_eficacia_diagnostica(especie_filtro="Felino")
    assert rep_fel["detalles_diagnosticos"] == []
    for d in rep_fel["detalles_diagnosticos"]:
        assert d["especie"] == "Felino"

    # Filtrar por Estado Diagnóstico
    rep_pat = service.generar_reporte_eficacia_diagnostica(estado_diagnostico_filtro="Hallazgo Patológico")
    for d in rep_pat["detalles_diagnosticos"]:
        assert d["estado_diagnostico"] == "Hallazgo Patológico"


def test_exportar_excel_eficacia_diagnostica(db_session):
    service = ReportesService(db_session)
    datos = service.generar_reporte_eficacia_diagnostica()
    excel_bytes = service.exportar_excel_eficacia_diagnostica(datos)

    assert isinstance(excel_bytes, bytes)
    assert len(excel_bytes) > 2000


def test_exportar_pdf_eficacia_diagnostica(db_session):
    service = ReportesService(db_session)
    datos = service.generar_reporte_eficacia_diagnostica()
    pdf_bytes = service.exportar_pdf_eficacia_diagnostica(datos)

    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes.startswith(b"%PDF")
    assert len(pdf_bytes) > 1000


def test_endpoint_eficacia_diagnostica_json(client):
    response = client.get("/api/v1/reportes/eficacia-diagnostica")
    assert response.status_code == 200
    data = response.json()
    assert "kpis" in data
    assert "desglose_por_especie" in data
    assert "top_analitos_criticos" in data
    assert "detalles_diagnosticos" in data
    assert data["filtros_disponibles"]["especies"] == ["Todas"]

    # Probar filtrado por query param especie
    res_esp = client.get("/api/v1/reportes/eficacia-diagnostica?especie=Felino")
    assert res_esp.status_code == 200
    data_esp = res_esp.json()
    for d in data_esp["detalles_diagnosticos"]:
        assert d["especie"] == "Felino"


def test_endpoint_eficacia_diagnostica_excel_y_pdf(client):
    res_excel = client.get("/api/v1/reportes/eficacia-diagnostica/excel")
    assert res_excel.status_code == 200
    assert "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" in res_excel.headers["content-type"]
    assert len(res_excel.content) > 2000

    res_pdf = client.get("/api/v1/reportes/eficacia-diagnostica/pdf")
    assert res_pdf.status_code == 200
    assert "application/pdf" in res_pdf.headers["content-type"]
    assert res_pdf.content.startswith(b"%PDF")



