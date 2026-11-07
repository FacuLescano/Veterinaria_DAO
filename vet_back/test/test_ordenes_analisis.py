def test_solicitar_analisis_us06_exitoso(client, datos_prueba):
    """US-06: Un veterinario solicita análisis para una consulta médica."""
    cuerpo = {
        "consulta_id": datos_prueba["consulta_id"],
        "veterinario_id": datos_prueba["veterinario_id"],
        "observaciones": "Control pre-quirúrgico",
        "detalles": [
            {
                "tipo_analisis_id": datos_prueba["tipo_analisis_id"],
                "indicaciones": "Ayuno de 12 horas",
            }
        ],
    }

    respuesta = client.post("/api/v1/ordenes-analisis/solicitar", json=cuerpo)
    assert respuesta.status_code == 201

    orden = respuesta.json()
    assert orden["id"] is not None
    assert orden["estado"] == "solicitada"
    assert orden["consulta_id"] == datos_prueba["consulta_id"]
    assert len(orden["detalles"]) == 1
    assert orden["detalles"][0]["indicaciones"] == "Ayuno de 12 horas"


def test_solicitar_analisis_consulta_inexistente(client, datos_prueba):
    """US-06: Si la consulta médica no existe, debe retornar 404."""
    cuerpo = {
        "consulta_id": 99999,
        "detalles": [{"tipo_analisis_id": datos_prueba["tipo_analisis_id"]}],
    }

    respuesta = client.post("/api/v1/ordenes-analisis/solicitar", json=cuerpo)
    assert respuesta.status_code == 404
    assert "Consulta médica" in respuesta.json()["detail"]


def test_listar_analisis_por_consulta(client, datos_prueba):
    """US-06: Consultar los análisis solicitados para una consulta médica."""
    test_solicitar_analisis_us06_exitoso(client, datos_prueba)

    respuesta = client.get(f"/api/v1/consultas/{datos_prueba['consulta_id']}/analisis")
    assert respuesta.status_code == 200
    ordenes = respuesta.json()
    assert len(ordenes) >= 1
    assert ordenes[0]["consulta_id"] == datos_prueba["consulta_id"]


# ==============================================================================
# Pruebas para US-07: Crear Orden de Análisis, Trazabilidad e Historial
# ==============================================================================

def test_us07_crear_orden_incluye_paciente_y_solicitante(client, datos_prueba):
    """US-07: Crear la orden y verificar que incluya datos del paciente y veterinario."""
    cuerpo = {
        "consulta_id": datos_prueba["consulta_id"],
        "detalles": [{"tipo_analisis_id": datos_prueba["tipo_analisis_id"]}],
    }
    respuesta = client.post("/api/v1/ordenes-analisis", json=cuerpo)
    assert respuesta.status_code == 201
    orden = respuesta.json()

    assert orden["id"] is not None
    assert orden["estado"] == "solicitada"
    assert orden["paciente_nombre"] == "Firulais"
    assert orden["veterinario_nombre"] == "Dra. Lopez"


def test_us07_formalizar_orden_e_historial(client, datos_prueba):
    """US-07: Formalizar orden a 'en_preparacion' y consultar su historial."""
    # 1. Crear orden
    res_crear = client.post(
        "/api/v1/ordenes-analisis",
        json={
            "consulta_id": datos_prueba["consulta_id"],
            "detalles": [{"tipo_analisis_id": datos_prueba["tipo_analisis_id"]}],
        },
    )
    orden_id = res_crear.json()["id"]

    # 2. Formalizar pasando a 'en_preparacion'
    res_patch = client.patch(
        f"/api/v1/ordenes-analisis/{orden_id}/estado",
        json={
            "nuevo_estado": "en_preparacion",
            "motivo": "Muestras listas para extracción",
        },
    )
    assert res_patch.status_code == 200
    assert res_patch.json()["estado"] == "en_preparacion"

    # 3. Consultar historial
    res_historial = client.get(f"/api/v1/ordenes-analisis/{orden_id}/historial")
    assert res_historial.status_code == 200
    historial = res_historial.json()
    assert len(historial) == 2
    assert historial[0]["estado_nuevo"] == "solicitada"
    assert historial[1]["estado_anterior"] == "solicitada"
    assert historial[1]["estado_nuevo"] == "en_preparacion"
    assert historial[1]["motivo"] == "Muestras listas para extracción"


def test_us07_transicion_estado_invalida(client, datos_prueba):
    """US-07: Impedir transiciones de estado no permitidas."""
    res_crear = client.post(
        "/api/v1/ordenes-analisis",
        json={
            "consulta_id": datos_prueba["consulta_id"],
            "detalles": [{"tipo_analisis_id": datos_prueba["tipo_analisis_id"]}],
        },
    )
    orden_id = res_crear.json()["id"]

    # Intentar saltar directamente a 'con_resultados'
    res_bad = client.patch(
        f"/api/v1/ordenes-analisis/{orden_id}/estado",
        json={"nuevo_estado": "con_resultados"},
    )
    assert res_bad.status_code == 409
    assert "Transición no permitida" in res_bad.json()["detail"]
