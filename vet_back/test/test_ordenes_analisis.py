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


# ==============================================================================
# Pruebas para US-09: Asociar muestras con análisis
# ==============================================================================

def test_us09_asociar_muestra_a_multiples_analisis(client, datos_prueba):
    """US-09: Una misma muestra puede satisfacer múltiples análisis de la orden si es compatible."""
    # 1. Crear un segundo tipo de análisis
    res_tipo2 = client.post(
        "/api/v1/tipos-analisis",
        json={"nombre": "Perfil Bioquimico", "descripcion": "Glucosa, Urea, Creatinina"},
    )
    tipo2_id = res_tipo2.json()["id"]

    # 2. Crear orden con 2 análisis solicitados
    res_orden = client.post(
        "/api/v1/ordenes-analisis",
        json={
            "consulta_id": datos_prueba["consulta_id"],
            "detalles": [
                {"tipo_analisis_id": datos_prueba["tipo_analisis_id"]},
                {"tipo_analisis_id": tipo2_id},
            ],
        },
    )
    orden = res_orden.json()
    orden_id = orden["id"]
    detalles = orden["detalles"]
    assert len(detalles) == 2

    # 3. Registrar una sola muestra de sangre
    res_muestra = client.post(
        "/api/v1/muestras",
        json={
            "codigo_etiqueta": "TUBO-MULTI-01",
            "orden_id": orden_id,
            "tipo_muestra_id": datos_prueba["tipo_muestra_id"],
            "responsable_extraccion": "Dra. Lopez",
        },
    )
    muestra_id = res_muestra.json()["id"]

    # 4. Asociar la misma muestra a ambos análisis de la orden
    res_asoc = client.post(
        f"/api/v1/ordenes-analisis/{orden_id}/asociar-muestra",
        json={
            "muestra_id": muestra_id,
            "detalle_ids": [detalles[0]["id"], detalles[1]["id"]],
            "observaciones": "Muestra suficiente para hemograma y bioquímica",
        },
    )
    assert res_asoc.status_code == 200
    datos_asoc = res_asoc.json()
    assert len(datos_asoc["detalles_asociados"]) == 2

    # 5. Comprobar que no quedan análisis pendientes de muestra en esta orden
    res_pendientes = client.get(f"/api/v1/ordenes-analisis/{orden_id}/analisis-pendientes")
    assert res_pendientes.status_code == 200
    assert len(res_pendientes.json()) == 0


def test_us09_rechaza_asociar_muestra_ya_enviada(client, datos_prueba):
    from app.models.orden_analisis import Muestra
    from test.conftest import TestingSessionLocal

    orden_res = client.post("/api/v1/ordenes-analisis", json={
        "consulta_id": datos_prueba["consulta_id"],
        "detalles": [{"tipo_analisis_id": datos_prueba["tipo_analisis_id"]}],
    })
    orden_id = orden_res.json()["id"]
    detalle_id = orden_res.json()["detalles"][0]["id"]
    muestra_res = client.post("/api/v1/muestras", json={
        "codigo_etiqueta": "TUBO-ENVIADO-01",
        "orden_id": orden_id,
        "tipo_muestra_id": datos_prueba["tipo_muestra_id"],
        "responsable_extraccion": "Dra. Lopez",
    })
    muestra_id = muestra_res.json()["id"]

    db = TestingSessionLocal()
    try:
        db.get(Muestra, muestra_id).estado = "enviada"
        db.commit()
    finally:
        db.close()

    asociacion = client.post(f"/api/v1/ordenes-analisis/{orden_id}/asociar-muestra", json={
        "muestra_id": muestra_id,
        "detalle_ids": [detalle_id],
    })
    assert asociacion.status_code == 409
    assert "no fueron empaquetadas ni enviadas" in asociacion.json()["detail"]


def test_us09_validar_incompatibilidad_tipo_muestra(client, datos_prueba):
    """US-09: No permite asociar una muestra biológica incompatible con el análisis solicitado."""
    # 1. Configurar que el tipo de análisis (Hemograma) solo acepta Sangre con EDTA
    res_compat = client.post(
        f"/api/v1/tipos-analisis/{datos_prueba['tipo_analisis_id']}/compatibilidad",
        json={"tipos_muestra_ids": [datos_prueba["tipo_muestra_id"]]},
    )
    assert res_compat.status_code == 200

    # 2. Registrar un tipo de muestra diferente (Orina)
    res_tipo_orina = client.post(
        "/api/v1/tipos-muestra",
        json={"nombre": "Muestra de Orina", "descripcion": "Frasco estéril de orina"},
    )
    tipo_orina_id = res_tipo_orina.json()["id"]

    # 3. Crear orden con Hemograma
    res_orden = client.post(
        "/api/v1/ordenes-analisis",
        json={
            "consulta_id": datos_prueba["consulta_id"],
            "detalles": [{"tipo_analisis_id": datos_prueba["tipo_analisis_id"]}],
        },
    )
    orden_id = res_orden.json()["id"]
    detalle_id = res_orden.json()["detalles"][0]["id"]

    # 4. Registrar muestra de orina en la orden
    res_muestra_orina = client.post(
        "/api/v1/muestras",
        json={
            "codigo_etiqueta": "FRASCO-ORINA-01",
            "orden_id": orden_id,
            "tipo_muestra_id": tipo_orina_id,
            "responsable_extraccion": "Enfermero Juan",
        },
    )
    muestra_orina_id = res_muestra_orina.json()["id"]

    # 5. Intentar asociar la muestra de orina con el Hemograma -> debe ser rechazada (400)
    res_invalida = client.post(
        f"/api/v1/ordenes-analisis/{orden_id}/asociar-muestra",
        json={
            "muestra_id": muestra_orina_id,
            "detalle_ids": [detalle_id],
        },
    )
    assert res_invalida.status_code == 400
    assert "Incompatibilidad biológica" in res_invalida.json()["detail"]


def test_us09_identificar_analisis_pendientes_de_muestra(client, datos_prueba):
    """US-09: Identificar con precisión los análisis que aún no tienen una muestra asociada."""
    # 1. Crear segundo tipo de análisis
    res_tipo2 = client.post(
        "/api/v1/tipos-analisis",
        json={"nombre": "Urocultivo", "descripcion": "Cultivo bacteriológico de orina"},
    )
    tipo2_id = res_tipo2.json()["id"]

    # 2. Crear orden con 2 análisis
    res_orden = client.post(
        "/api/v1/ordenes-analisis",
        json={
            "consulta_id": datos_prueba["consulta_id"],
            "detalles": [
                {"tipo_analisis_id": datos_prueba["tipo_analisis_id"]},
                {"tipo_analisis_id": tipo2_id},
            ],
        },
    )
    orden = res_orden.json()
    orden_id = orden["id"]
    detalles = orden["detalles"]

    # Al inicio, ambos análisis están pendientes
    res_pendientes_ini = client.get(f"/api/v1/ordenes-analisis/{orden_id}/analisis-pendientes")
    assert len(res_pendientes_ini.json()) == 2

    # 3. Registrar muestra y asociar SOLO al primer análisis
    res_muestra = client.post(
        "/api/v1/muestras",
        json={
            "codigo_etiqueta": "TUBO-SOLO-UNO",
            "orden_id": orden_id,
            "tipo_muestra_id": datos_prueba["tipo_muestra_id"],
            "responsable_extraccion": "Dra. Lopez",
        },
    )
    client.post(
        f"/api/v1/ordenes-analisis/{orden_id}/asociar-muestra",
        json={
            "muestra_id": res_muestra.json()["id"],
            "detalle_ids": [detalles[0]["id"]],
        },
    )

    # 4. Verificar que ahora solo queda 1 pendiente (el segundo análisis)
    res_pendientes_fin = client.get(f"/api/v1/ordenes-analisis/{orden_id}/analisis-pendientes")
    assert res_pendientes_fin.status_code == 200
    pendientes = res_pendientes_fin.json()
    assert len(pendientes) == 1
    assert pendientes[0]["id"] == detalles[1]["id"]
    assert pendientes[0]["tipo_analisis"]["nombre"] == "Urocultivo"


# ==============================================================================
# Pruebas para US-10: Consultar estado de la orden y sus muestras
# ==============================================================================

def test_us10_consultar_estado_orden_y_muestras(client, datos_prueba):
    """US-10: Consultar el estado consolidado de la orden distinguiendo muestras listas vs con inconvenientes."""
    # 1. Crear tipo de análisis secundario y orden con 2 análisis
    res_tipo2 = client.post(
        "/api/v1/tipos-analisis",
        json={"nombre": "Glucemia", "descripcion": "Dosaje de glucosa en sangre"},
    )
    tipo2_id = res_tipo2.json()["id"]

    res_orden = client.post(
        "/api/v1/ordenes-analisis",
        json={
            "consulta_id": datos_prueba["consulta_id"],
            "detalles": [
                {"tipo_analisis_id": datos_prueba["tipo_analisis_id"]},
                {"tipo_analisis_id": tipo2_id},
            ],
        },
    )
    orden_id = res_orden.json()["id"]
    detalles = res_orden.json()["detalles"]

    # 2. Registrar Muestra 1 y pasarla a lista_para_envio
    res_m1 = client.post(
        "/api/v1/muestras",
        json={
            "codigo_etiqueta": "TUBO-LISTO-01",
            "orden_id": orden_id,
            "tipo_muestra_id": datos_prueba["tipo_muestra_id"],
            "responsable_extraccion": "Dra. Lopez",
        },
    )
    m1_id = res_m1.json()["id"]
    client.post(
        f"/api/v1/ordenes-analisis/{orden_id}/asociar-muestra",
        json={"muestra_id": m1_id, "detalle_ids": [detalles[0]["id"]]},
    )
    client.patch(
        f"/api/v1/muestras/{m1_id}/estado",
        json={
            "nuevo_estado": "lista_para_envio",
            "responsable": "Bioq. Gomez",
            "motivo": "Acondicionada térmicamente a 4°C",
        },
    )

    # 3. Registrar Muestra 2 y marcarla con inconveniente (ej: hemolizada / rota)
    res_m2 = client.post(
        "/api/v1/muestras",
        json={
            "codigo_etiqueta": "TUBO-PROBLEMA-02",
            "orden_id": orden_id,
            "tipo_muestra_id": datos_prueba["tipo_muestra_id"],
            "responsable_extraccion": "Enfermero Juan",
        },
    )
    m2_id = res_m2.json()["id"]
    client.post(
        f"/api/v1/ordenes-analisis/{orden_id}/asociar-muestra",
        json={"muestra_id": m2_id, "detalle_ids": [detalles[1]["id"]]},
    )
    client.patch(
        f"/api/v1/muestras/{m2_id}/estado",
        json={
            "nuevo_estado": "con_inconveniente",
            "responsable": "Bioq. Gomez",
            "motivo": "Muestra coagulada, no apta para procesamiento",
        },
    )

    # 4. Consultar seguimiento consolidado de la orden
    res_seg = client.get(f"/api/v1/ordenes-analisis/{orden_id}/seguimiento")
    assert res_seg.status_code == 200
    seguimiento = res_seg.json()

    assert seguimiento["orden_id"] == orden_id
    assert seguimiento["paciente_nombre"] == "Firulais"
    assert seguimiento["resumen_muestras"]["total"] == 2
    assert seguimiento["resumen_muestras"]["listas_para_envio"] == 1
    assert seguimiento["resumen_muestras"]["con_inconvenientes"] == 1
    assert len(seguimiento["muestras_listas_para_enviar"]) == 1
    assert seguimiento["muestras_listas_para_enviar"][0]["codigo_etiqueta"] == "TUBO-LISTO-01"
    assert len(seguimiento["muestras_con_inconvenientes"]) == 1
    assert seguimiento["muestras_con_inconvenientes"][0]["codigo_etiqueta"] == "TUBO-PROBLEMA-02"
    assert seguimiento["lista_para_despacho"] is False


def test_us10_trazabilidad_cambio_estado_muestra(client, datos_prueba):
    """US-10: Conservar los cambios de estado de la muestra con fecha, responsable y motivo."""
    res_orden = client.post(
        "/api/v1/ordenes-analisis",
        json={
            "consulta_id": datos_prueba["consulta_id"],
            "detalles": [{"tipo_analisis_id": datos_prueba["tipo_analisis_id"]}],
        },
    )
    orden_id = res_orden.json()["id"]

    res_muestra = client.post(
        "/api/v1/muestras",
        json={
            "codigo_etiqueta": "TUBO-TRAZABILIDAD",
            "orden_id": orden_id,
            "tipo_muestra_id": datos_prueba["tipo_muestra_id"],
            "responsable_extraccion": "Dra. Lopez",
        },
    )
    muestra_id = res_muestra.json()["id"]

    # 1. Cambiar a 'pendiente_preparacion'
    res_p1 = client.patch(
        f"/api/v1/muestras/{muestra_id}/estado",
        json={
            "nuevo_estado": "pendiente_preparacion",
            "responsable": "Asistente Clara",
            "motivo": "En espera de centrifugado",
        },
    )
    assert res_p1.status_code == 200
    assert res_p1.json()["estado"] == "pendiente_preparacion"

    # 2. Cambiar a 'lista_para_envio'
    res_p2 = client.patch(
        f"/api/v1/muestras/{muestra_id}/estado",
        json={
            "nuevo_estado": "lista_para_envio",
            "responsable": "Bioq. Gomez",
            "motivo": "Centrifugado finalizado y rotulada",
        },
    )
    assert res_p2.status_code == 200
    assert res_p2.json()["estado"] == "lista_para_envio"

    # 3. Consultar historial de la muestra
    res_hist = client.get(f"/api/v1/muestras/{muestra_id}/historial")
    assert res_hist.status_code == 200
    historial = res_hist.json()
    assert len(historial) == 3
    assert historial[0]["estado_nuevo"] == "extraida"
    assert historial[1]["estado_nuevo"] == "pendiente_preparacion"
    assert historial[1]["responsable"] == "Asistente Clara"
    assert historial[2]["estado_nuevo"] == "lista_para_envio"
    assert historial[2]["responsable"] == "Bioq. Gomez"


def test_us10_impedir_enviar_muestra_sin_informacion_obligatoria(client, datos_prueba):
    """US-10: Impedir enviar muestras sin información obligatoria (ej: sin análisis asignado)."""
    res_orden = client.post(
        "/api/v1/ordenes-analisis",
        json={
            "consulta_id": datos_prueba["consulta_id"],
            "detalles": [{"tipo_analisis_id": datos_prueba["tipo_analisis_id"]}],
        },
    )
    orden_id = res_orden.json()["id"]

    # Muestra creada pero sin asociar a ningún análisis
    res_muestra = client.post(
        "/api/v1/muestras",
        json={
            "codigo_etiqueta": "TUBO-SIN-ANALISIS",
            "orden_id": orden_id,
            "tipo_muestra_id": datos_prueba["tipo_muestra_id"],
            "responsable_extraccion": "Dra. Lopez",
        },
    )
    muestra_id = res_muestra.json()["id"]

    # Intentar pasar a 'enviada' sin estar asociada a ningún análisis
    res_envio = client.patch(
        f"/api/v1/muestras/{muestra_id}/estado",
        json={
            "nuevo_estado": "enviada",
            "responsable": "Logística",
        },
    )
    assert res_envio.status_code == 400
    assert "No se permite enviar una muestra que no esté asociada a ningún análisis" in res_envio.json()["detail"]



