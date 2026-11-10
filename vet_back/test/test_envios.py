from datetime import datetime, timezone


def _preparar_envio(client, datos_prueba, sufijo):
    orden_response = client.post(
        "/api/v1/ordenes-analisis",
        json={
            "consulta_id": datos_prueba["consulta_id"],
            "detalles": [{"tipo_analisis_id": datos_prueba["tipo_analisis_id"]}],
        },
    )
    assert orden_response.status_code == 201
    orden = orden_response.json()

    muestra_response = client.post(
        "/api/v1/muestras",
        json={
            "codigo_etiqueta": f"MUESTRA-{sufijo}",
            "orden_id": orden["id"],
            "tipo_muestra_id": datos_prueba["tipo_muestra_id"],
            "responsable_extraccion": "Dra. Lopez",
            "condiciones_conservacion": "Refrigerar a 4°C",
        },
    )
    assert muestra_response.status_code == 201
    muestra = muestra_response.json()

    asociacion_response = client.post(
        f"/api/v1/ordenes-analisis/{orden['id']}/asociar-muestra",
        json={
            "muestra_id": muestra["id"],
            "detalle_ids": [orden["detalles"][0]["id"]],
        },
    )
    assert asociacion_response.status_code == 200

    estado_response = client.patch(
        f"/api/v1/muestras/{muestra['id']}/estado",
        json={
            "nuevo_estado": "lista_para_envio",
            "responsable": "Personal de prueba",
            "motivo": "Muestra acondicionada",
        },
    )
    assert estado_response.status_code == 200

    conservadora_response = client.post(
        "/api/v1/conservadoras",
        json={"codigo": f"CONS-{sufijo}", "descripcion": "Conservadora refrigerada"},
    )
    assert conservadora_response.status_code == 201
    conservadora = conservadora_response.json()

    envio_response = client.post(
        "/api/v1/envios",
        json={
            "origen": "Clínica de prueba",
            "destino": "Laboratorio externo",
            "condiciones_empaquetado": "Muestra protegida en bolsa biosegura y refrigerada",
            "conservadoras": [
                {
                    "conservadora_id": conservadora["id"],
                    "muestra_ids": [muestra["id"]],
                }
            ],
        },
    )
    assert envio_response.status_code == 201
    envio = envio_response.json()

    precinto_response = client.post(
        f"/api/v1/envios/{envio['id']}/precintos",
        json={
            "codigo": f"PREC-{sufijo}",
            "conservadora_id": conservadora["id"],
            "colocado_por": "Personal de prueba",
        },
    )
    assert precinto_response.status_code == 201

    return envio["id"], muestra["id"], conservadora["id"], f"PREC-{sufijo}"


def _despachar(client, envio_id):
    return client.post(
        f"/api/v1/envios/{envio_id}/despachar",
        json={
            "responsable_despacho": "Responsable de prueba",
            "transportista": "Transporte de prueba",
            "fecha_despacho": datetime.now(timezone.utc).isoformat(),
        },
    )


def test_remito_imprimible_y_condiciones_empaquetado(client, datos_prueba):
    envio_id, muestra_id, conservadora_id, codigo_precinto = _preparar_envio(
        client, datos_prueba, "PRINT"
    )

    antes_despacho = client.get(f"/api/v1/envios/{envio_id}").json()
    assert antes_despacho["estado"] == "en_preparacion"
    assert "bolsa biosegura" in antes_despacho["condiciones_empaquetado"]

    verificacion = client.post(
        f"/api/v1/envios/{envio_id}/verificaciones-precinto",
        json={
            "conservadora_id": conservadora_id,
            "codigo_observado": codigo_precinto,
            "resultado": "integro",
            "responsable": "Personal de prueba",
        },
    )
    assert verificacion.status_code == 201
    assert verificacion.json()["precintos"][0]["verificaciones"][0]["resultado"] == "integro"

    despacho = _despachar(client, envio_id)
    assert despacho.status_code == 200
    assert despacho.json()["estado"] == "despachado"
    assert despacho.json()["muestras"][0]["id"] == muestra_id

    remito = client.get(f"/api/v1/envios/{envio_id}/remito")
    assert remito.status_code == 200
    assert remito.json()["contenido"]["condiciones_empaquetado"] == (
        "Muestra protegida en bolsa biosegura y refrigerada"
    )

    impresion = client.get(f"/api/v1/envios/{envio_id}/remito/impresion")
    assert impresion.status_code == 200
    assert "Imprimir remito" in impresion.text
    assert codigo_precinto in impresion.text


def test_anomalia_de_precinto_crea_incidencia_y_bloquea_despacho(client, datos_prueba):
    envio_id, _, conservadora_id, codigo_precinto = _preparar_envio(
        client, datos_prueba, "SEAL"
    )

    verificacion_rota = client.post(
        f"/api/v1/envios/{envio_id}/verificaciones-precinto",
        json={
            "conservadora_id": conservadora_id,
            "codigo_observado": codigo_precinto,
            "resultado": "roto",
            "responsable": "Personal de prueba",
            "observaciones": "Precinto dañado antes de la salida",
        },
    )
    assert verificacion_rota.status_code == 201
    assert verificacion_rota.json()["incidencias"][0]["tipo"] == "precinto_roto"

    despacho_bloqueado = _despachar(client, envio_id)
    assert despacho_bloqueado.status_code == 409

    envio_actualizado = client.get(f"/api/v1/envios/{envio_id}")
    assert envio_actualizado.status_code == 200
    assert envio_actualizado.json()["estado"] == "en_preparacion"
