"""Tests de integración para los cuatro reportes simplificados."""

from datetime import datetime, timedelta
from uuid import uuid4

import pytest
from test.conftest import TestingSessionLocal
from app.services.reportes_service import ReportesService
from app.models.orden_analisis import AsociacionDetalleMuestra, DetalleOrdenAnalisis, Muestra, OrdenAnalisis
from app.models.recepcion import ResultadoAnalisis


def test_indicadores_usan_muestras_resultados_recepcion_y_consultas_reales(db_session, datos_prueba):
    orden = OrdenAnalisis(consulta_id=datos_prueba["consulta_id"], veterinario_id=datos_prueba["veterinario_id"])
    db_session.add(orden)
    db_session.flush()
    detalle = DetalleOrdenAnalisis(orden_id=orden.id, tipo_analisis_id=datos_prueba["tipo_analisis_id"])
    muestra = Muestra(
        codigo_etiqueta=f"M-{uuid4().hex[:8]}", orden_id=orden.id,
        tipo_muestra_id=datos_prueba["tipo_muestra_id"], fecha_extraccion=datetime.now() - timedelta(days=1),
        responsable_extraccion="Equipo clínico", condiciones_conservacion="Refrigerada", estado="recibida",
    )
    db_session.add_all([detalle, muestra])
    db_session.flush()
    db_session.add(AsociacionDetalleMuestra(detalle_id=detalle.id, muestra_id=muestra.id))
    db_session.commit()

    service = ReportesService(db_session)
    reporte_muestras = service.generar_reporte_tiempos_sla()
    assert reporte_muestras["kpis"]["total_muestras_extraidas"] == 1
    assert reporte_muestras["kpis"]["muestras_con_resultado"] == 0
    assert reporte_muestras["kpis"]["muestras_sin_resultado"] == 1
    assert reporte_muestras["distribucion_tipo_muestra"] == [{"tipo_muestra": "Sangre con EDTA", "cantidad": 1}]

    reporte_recepcion = service.generar_reporte_muestras_rechazadas()
    assert reporte_recepcion["kpis"]["muestras_aceptadas"] == 1
    assert reporte_recepcion["kpis"]["muestras_pendientes"] == 0
    assert reporte_recepcion["kpis"]["muestras_rechazadas"] == 0

    reporte_clinico = service.generar_reporte_rendimiento_clinico()
    assert reporte_clinico["kpis"]["total_consultas_realizadas"] == 1
    assert reporte_clinico["kpis"]["turnos_atendidos"] == 0
    assert reporte_clinico["kpis"]["porcentaje_consultas_con_orden"] == 100.0

    resultado = ResultadoAnalisis(
        id=str(uuid4()), orden_id=str(orden.id), detalle_orden_id=str(detalle.id), muestra_id=str(muestra.id),
        paciente_id=str(orden.consulta.pet_id), fecha_recepcion=datetime.now(), procedencia="Laboratorio",
        estado="recibido", datos={}, registrado_por="Laboratorio",
    )
    db_session.add(resultado)
    db_session.commit()

    reporte_muestras = service.generar_reporte_tiempos_sla()
    assert reporte_muestras["kpis"]["muestras_con_resultado"] == 1
    assert reporte_muestras["kpis"]["muestras_sin_resultado"] == 0
    assert reporte_muestras["kpis"]["porcentaje_con_resultado"] == 100.0
    reporte_resultados = service.generar_reporte_eficacia_diagnostica()
    assert reporte_resultados["kpis"]["resultados_recibidos"] == 1
    assert reporte_resultados["kpis"]["analisis_pendientes"] == 0


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
    assert "distribucion_tipo_muestra" in reporte
    assert "comparacion_muestras" in reporte

    kpis = reporte["kpis"]
    assert kpis["total_muestras_extraidas"] == 0
    assert kpis["muestras_con_resultado"] == 0
    assert kpis["muestras_sin_resultado"] == 0
    assert kpis["porcentaje_con_resultado"] is None


def test_filtros_reporte_tiempos_sla(db_session):
    service = ReportesService(db_session)
    reporte_tipo = service.generar_reporte_tiempos_sla(tipo_analisis_filtro="Sangre con EDTA")
    assert reporte_tipo["kpis"]["total_muestras_extraidas"] == 0


def test_exportar_excel(db_session):
    service = ReportesService(db_session)
    datos = service.generar_reporte_tiempos_sla()
    excel_bytes = service.exportar_excel(datos)

    assert isinstance(excel_bytes, bytes)
    assert excel_bytes.startswith(b"PK")


def test_exportar_pdf(db_session):
    service = ReportesService(db_session)
    datos = service.generar_reporte_tiempos_sla()
    pdf_bytes = service.exportar_pdf(datos)

    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes.startswith(b"%PDF")
    assert len(pdf_bytes) > 500


def test_endpoint_reporte_json(client):
    response = client.get("/api/v1/reportes/tiempos-sla")
    assert response.status_code == 200
    data = response.json()
    assert "kpis" in data
    assert "distribucion_tipo_muestra" in data
    assert "comparacion_muestras" in data


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
    assert "distribucion_estados_recepcion" in reporte
    assert "tiempos_recepcion" in reporte

    kpis = reporte["kpis"]
    assert kpis["muestras_pendientes"] == 0
    assert kpis["muestras_rechazadas"] == 0
    assert kpis["muestras_aceptadas"] == 0
    assert kpis["porcentaje_aceptadas"] is None
    assert kpis["porcentaje_rechazadas"] is None


def test_filtros_muestras_rechazadas(db_session):
    service = ReportesService(db_session)
    solo_rechazadas = service.generar_reporte_muestras_rechazadas(estado_filtro="Rechazada")
    assert solo_rechazadas["kpis"]["muestras_rechazadas"] == 0

    solo_aceptadas = service.generar_reporte_muestras_rechazadas(estado_filtro="Aceptada")
    assert solo_aceptadas["kpis"]["muestras_aceptadas"] == 0


def test_exportar_excel_muestras_rechazadas(db_session):
    service = ReportesService(db_session)
    datos = service.generar_reporte_muestras_rechazadas()
    excel_bytes = service.exportar_excel_muestras_rechazadas(datos)

    assert isinstance(excel_bytes, bytes)
    assert excel_bytes.startswith(b"PK")


def test_exportar_pdf_muestras_rechazadas(db_session):
    service = ReportesService(db_session)
    datos = service.generar_reporte_muestras_rechazadas()
    pdf_bytes = service.exportar_pdf_muestras_rechazadas(datos)

    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes.startswith(b"%PDF")
    assert len(pdf_bytes) > 500


def test_endpoint_muestras_rechazadas_json(client):
    response = client.get("/api/v1/reportes/muestras-rechazadas")
    assert response.status_code == 200
    data = response.json()
    assert "kpis" in data
    assert "distribucion_estados_recepcion" in data
    assert data["filtros_disponibles"]["estados"] == ["Todos", "Pendiente", "Aceptada", "Rechazada"]


def test_endpoint_muestras_rechazadas_excel(client):
    response = client.get("/api/v1/reportes/muestras-rechazadas/excel")
    assert response.status_code == 200
    assert "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" in response.headers["content-type"]
    assert response.content.startswith(b"PK")


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
    assert "distribucion_estados_turno" in reporte
    assert "actividad_por_hora" in reporte
    assert "comparacion_consultas_ordenes" in reporte
    assert "filtros_disponibles" in reporte

    kpis = reporte["kpis"]
    assert kpis["turnos_atendidos"] == 0
    assert kpis["turnos_cancelados"] == 0
    assert kpis["turnos_ausentes"] == 0
    assert kpis["total_consultas_realizadas"] == 0
    assert kpis["porcentaje_consultas_con_orden"] is None

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
    assert rep_vet["rendimiento_veterinarios"] == []

    # Filtro por derivación
    rep_deriv = service.generar_reporte_rendimiento_clinico(derivacion_filtro="Con Derivación")
    assert rep_deriv["kpis"]["total_consultas_realizadas"] == 0

    rep_sin_deriv = service.generar_reporte_rendimiento_clinico(derivacion_filtro="Sin Derivación")
    assert rep_sin_deriv["kpis"]["total_consultas_realizadas"] == 0


def test_exportar_excel_rendimiento_clinico(db_session):
    service = ReportesService(db_session)
    datos = service.generar_reporte_rendimiento_clinico()
    excel_bytes = service.exportar_excel_rendimiento_clinico(datos)

    assert isinstance(excel_bytes, bytes)
    assert excel_bytes.startswith(b"PK")


def test_exportar_pdf_rendimiento_clinico(db_session):
    service = ReportesService(db_session)
    datos = service.generar_reporte_rendimiento_clinico()
    pdf_bytes = service.exportar_pdf_rendimiento_clinico(datos)

    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes.startswith(b"%PDF")
    assert len(pdf_bytes) > 500


def test_endpoint_rendimiento_clinico_json(client):
    response = client.get("/api/v1/reportes/rendimiento-clinico")
    assert response.status_code == 200
    data = response.json()
    assert "kpis" in data
    assert "rendimiento_veterinarios" in data
    assert "actividad_por_hora" in data
    assert data["filtros_disponibles"]["veterinarios"] == ["Todos"]

    # Probar filtrado por veterinario
    res_vet = client.get("/api/v1/reportes/rendimiento-clinico?veterinario=Lucas+Ferrara")
    assert res_vet.status_code == 200
    data_vet = res_vet.json()
    assert data_vet["rendimiento_veterinarios"] == []


def test_endpoint_rendimiento_clinico_excel(client):
    response = client.get("/api/v1/reportes/rendimiento-clinico/excel")
    assert response.status_code == 200
    assert "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" in response.headers["content-type"]
    assert response.content.startswith(b"PK")


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
    assert "evolucion_resultados" in reporte
    assert "estado_resultados" in reporte
    assert "tiempos_respuesta" in reporte
    assert "antiguedad_pendientes_dias" in reporte

    kpis = reporte["kpis"]
    assert kpis["resultados_recibidos"] == 0
    assert kpis["analisis_pendientes"] == 0
    assert kpis["porcentaje_con_resultado"] is None
    assert kpis["tiempo_promedio_respuesta_horas"] is None


def test_filtros_reporte_eficacia_diagnostica(db_session):
    service = ReportesService(db_session)

    # Filtrar por especie Canino
    rep_can = service.generar_reporte_eficacia_diagnostica(especie_filtro="Canino")
    assert rep_can["kpis"]["resultados_recibidos"] == 0

    # Filtrar por especie Felino
    rep_fel = service.generar_reporte_eficacia_diagnostica(especie_filtro="Felino")
    assert rep_fel["kpis"]["resultados_recibidos"] == 0

    # Filtrar por Estado Diagnóstico
    rep_pat = service.generar_reporte_eficacia_diagnostica(estado_diagnostico_filtro="Hallazgo Patológico")
    assert rep_pat["kpis"]["resultados_recibidos"] == 0


def test_exportar_excel_eficacia_diagnostica(db_session):
    service = ReportesService(db_session)
    datos = service.generar_reporte_eficacia_diagnostica()
    excel_bytes = service.exportar_excel_eficacia_diagnostica(datos)

    assert isinstance(excel_bytes, bytes)
    assert excel_bytes.startswith(b"PK")


def test_exportar_pdf_eficacia_diagnostica(db_session):
    service = ReportesService(db_session)
    datos = service.generar_reporte_eficacia_diagnostica()
    pdf_bytes = service.exportar_pdf_eficacia_diagnostica(datos)

    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes.startswith(b"%PDF")
    assert len(pdf_bytes) > 500


def test_endpoint_eficacia_diagnostica_json(client):
    response = client.get("/api/v1/reportes/eficacia-diagnostica")
    assert response.status_code == 200
    data = response.json()
    assert "kpis" in data
    assert "evolucion_resultados" in data
    assert data["filtros_disponibles"]["tipos_analisis"] == ["Todos"]


def test_endpoint_eficacia_diagnostica_excel_y_pdf(client):
    res_excel = client.get("/api/v1/reportes/eficacia-diagnostica/excel")
    assert res_excel.status_code == 200
    assert "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" in res_excel.headers["content-type"]
    assert res_excel.content.startswith(b"PK")

    res_pdf = client.get("/api/v1/reportes/eficacia-diagnostica/pdf")
    assert res_pdf.status_code == 200
    assert "application/pdf" in res_pdf.headers["content-type"]
    assert res_pdf.content.startswith(b"%PDF")



