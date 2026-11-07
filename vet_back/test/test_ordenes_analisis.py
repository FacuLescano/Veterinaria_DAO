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


# ==============================================================================
# Pruebas para US-08: Registrar extracción de muestra
# ==============================================================================

def test_us08_registrar_extraccion_muestra_exitosa(client, datos_prueba):
    """US-08: Registrar la extracción de una muestra con su etiqueta física, responsable y condiciones."""
    # 1. Crear una orden de análisis previa
    res_orden = client.post(
        "/api/v1/ordenes-analisis",
        json={
            "consulta_id": datos_prueba["consulta_id"],
            "detalles": [{"tipo_analisis_id": datos_prueba["tipo_analisis_id"]}],
        },
    )
    orden_id = res_orden.json()["id"]

    # 2. Registrar la extracción de la muestra
    cuerpo_muestra = {
        "codigo_etiqueta": "MUESTRA-2026-001",
        "orden_id": orden_id,
        "tipo_muestra_id": datos_prueba["tipo_muestra_id"],
        "responsable_extraccion": "Dra. Lopez",
        "observaciones_calidad": "Muestra clara, sin hemólisis",
    }
    res_muestra = client.post("/api/v1/muestras", json=cuerpo_muestra)
    assert res_muestra.status_code == 201

    muestra = res_muestra.json()
    assert muestra["id"] is not None
    assert muestra["codigo_etiqueta"] == "MUESTRA-2026-001"
    assert muestra["orden_id"] == orden_id
    assert muestra["estado"] == "extraida"
    # Condiciones por defecto heredadas del tipo de muestra
    assert muestra["condiciones_conservacion"] == "Refrigerar a 4°C"
    assert muestra["tipo_muestra"]["nombre"] == "Sangre con EDTA"
    assert len(muestra["historial"]) == 1
    assert muestra["historial"][0]["estado_nuevo"] == "extraida"

    # 3. Consultar las muestras vinculadas a la orden
    res_list = client.get(f"/api/v1/ordenes-analisis/{orden_id}/muestras")
    assert res_list.status_code == 200
    muestras_orden = res_list.json()
    assert len(muestras_orden) == 1
    assert muestras_orden[0]["codigo_etiqueta"] == "MUESTRA-2026-001"


def test_us08_muestra_codigo_duplicado_rechazado(client, datos_prueba):
    """US-08: El código de etiqueta física debe ser único (no duplicado)."""
    res_orden = client.post(
        "/api/v1/ordenes-analisis",
        json={
            "consulta_id": datos_prueba["consulta_id"],
            "detalles": [{"tipo_analisis_id": datos_prueba["tipo_analisis_id"]}],
        },
    )
    orden_id = res_orden.json()["id"]

    cuerpo = {
        "codigo_etiqueta": "TUBO-REPETIDO",
        "orden_id": orden_id,
        "tipo_muestra_id": datos_prueba["tipo_muestra_id"],
        "responsable_extraccion": "Enfermero Juan",
    }

    # Primera vez: exitoso
    res1 = client.post("/api/v1/muestras", json=cuerpo)
    assert res1.status_code == 201

    # Segunda vez: conflicto por código duplicado
    res2 = client.post("/api/v1/muestras", json=cuerpo)
    assert res2.status_code == 409
    assert "Ya existe una muestra registrada con el código de etiqueta" in res2.json()["detail"]


def test_us08_muestra_orden_inexistente(client, datos_prueba):
    """US-08: No se puede registrar muestra para una orden que no existe."""
    cuerpo = {
        "codigo_etiqueta": "TUBO-INEXISTENTE",
        "orden_id": 99999,
        "tipo_muestra_id": datos_prueba["tipo_muestra_id"],
        "responsable_extraccion": "Dra. Lopez",
    }
    res = client.post("/api/v1/muestras", json=cuerpo)
    assert res.status_code == 404
    assert "Orden de análisis" in res.json()["detail"]

