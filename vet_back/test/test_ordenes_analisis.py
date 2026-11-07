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
