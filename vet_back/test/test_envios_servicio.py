from datetime import datetime, timezone

import pytest
from fastapi import HTTPException

from app.models.envio import Conservadora
from app.models.orden_analisis import (
    AsociacionDetalleMuestra,
    DetalleOrdenAnalisis,
    Muestra,
    OrdenAnalisis,
)
from app.models.paciente import Consulta
from app.schemas.envio import (
    ConservadoraCreate,
    DespachoCreate,
    EnvioCreate,
    EnvioRead,
    ContenidoConservadoraCreate,
    RegistroTemperaturaCreate,
    PrecintoCreate,
    VerificacionPrecintoCreate,
)
from app.services.envio_service import EnvioService
from test.conftest import TestingSessionLocal


def _preparar_datos(db, datos_prueba, sufijo, condicion="Refrigerar a 4°C"):
    consulta = db.get(Consulta, datos_prueba["consulta_id"])
    orden = OrdenAnalisis(
        consulta_id=consulta.id,
        veterinario_id=datos_prueba["veterinario_id"],
        estado="en_preparacion",
    )
    db.add(orden)
    db.flush()

    detalle = DetalleOrdenAnalisis(
        orden_id=orden.id,
        tipo_analisis_id=datos_prueba["tipo_analisis_id"],
        estado="solicitado",
    )
    db.add(detalle)
    db.flush()

    muestra = Muestra(
        codigo_etiqueta=f"MUESTRA-{sufijo}",
        orden_id=orden.id,
        tipo_muestra_id=datos_prueba["tipo_muestra_id"],
        responsable_extraccion="Dra. Lopez",
        condiciones_conservacion=condicion,
        estado="lista_para_envio",
    )
    db.add(muestra)
    db.flush()
    db.add(AsociacionDetalleMuestra(detalle_id=detalle.id, muestra_id=muestra.id))
    db.commit()
    return muestra


def test_registro_verificacion_remito_imprimible_y_trazabilidad(datos_prueba):
    db = TestingSessionLocal()
    try:
        muestra = _preparar_datos(db, datos_prueba, "SERVICE-01", "Refrigerada (2° a 8°C)")
        service = EnvioService(db)
        conservadora = service.registrar_conservadora(
            ConservadoraCreate(codigo="CONS-SERVICE-01", descripcion="Conservadora de prueba")
        )
        envio = service.crear_envio(
            EnvioCreate(
                origen="Clínica de prueba",
                destino="Laboratorio externo",
                condiciones_empaquetado="Bolsa biosegura y refrigeración a 4°C",
                conservadoras=[
                    ContenidoConservadoraCreate(
                        conservadora_id=conservadora.id,
                        muestra_ids=[muestra.id],
                    )
                ],
            )
        )
        assert muestra.estado == "empaquetada"
        assert muestra.historial[-1].estado_nuevo == "empaquetada"
        lectura_salida = RegistroTemperaturaCreate(
            conservadora_id=conservadora.id,
            temperatura_requerida_c=4,
            temperatura_medida_c=4.1,
            fecha_medicion=datetime.now(timezone.utc),
            responsable="Personal de prueba",
        )
        preparado = service.registrar_temperatura(envio["id"], lectura_salida)
        assert preparado["estado"] == "en_preparacion"
        assert preparado["registros_temperatura"][0].temperatura_medida_c == 4.1
        assert preparado["precintos"] == []
        service.registrar_precinto(
            envio["id"],
            PrecintoCreate(
                codigo="PREC-SERVICE-01",
                conservadora_id=conservadora.id,
                colocado_por="Personal de prueba",
            ),
        )
        with pytest.raises(HTTPException, match="antes de colocar el precinto") as error:
            service.registrar_temperatura(envio["id"], lectura_salida)
        assert error.value.status_code == 409
        verificado = service.verificar_precinto(
            envio["id"],
            VerificacionPrecintoCreate(
                conservadora_id=conservadora.id,
                codigo_observado="PREC-SERVICE-01",
                resultado="integro",
                responsable="Personal de prueba",
            ),
        )
        verificado_schema = EnvioRead.model_validate(verificado)
        assert verificado_schema.precintos[0].verificaciones[0].resultado == "integro"

        despacho = service.despachar_envio(
            envio["id"],
            DespachoCreate(
                responsable_despacho="Responsable de prueba",
                transportista="Transporte de prueba",
            ),
        )
        assert despacho["estado"] == "despachado"
        assert despacho["muestras"][0].estado == "enviada"
        assert despacho["registros_temperatura"][0].fecha_medicion <= despacho["precintos"][0].fecha_colocacion
        assert "Bolsa biosegura" in despacho["remito"]["contenido"]["condiciones_empaquetado"]
        html = service.obtener_remito_html(envio["id"])
        assert "Imprimir remito" in html
        assert "PREC-SERVICE-01" in html

        with pytest.raises(HTTPException, match="durante la preparación") as error:
            service.registrar_temperatura(envio["id"], lectura_salida)
        assert error.value.status_code == 409
        assert len(despacho["registros_temperatura"]) == 1
        assert despacho["registros_temperatura"][0].temperatura_requerida_c == 4
    finally:
        db.close()


def test_precinto_anomalo_genera_incidencia_y_bloquea_despacho(datos_prueba):
    db = TestingSessionLocal()
    try:
        _preparar_datos(db, datos_prueba, "SERVICE-02")
        service = EnvioService(db)
        conservadora = service.registrar_conservadora(
            ConservadoraCreate(codigo="CONS-SERVICE-02")
        )
        # La muestra de este envío se recupera de la orden de prueba recién creada.
        muestra = db.query(Muestra).filter(Muestra.codigo_etiqueta == "MUESTRA-SERVICE-02").one()
        envio = service.crear_envio(
            EnvioCreate(
                origen="Clínica de prueba",
                destino="Laboratorio externo",
                condiciones_empaquetado="Empaque sellado",
                conservadoras=[
                    ContenidoConservadoraCreate(
                        conservadora_id=conservadora.id,
                        muestra_ids=[muestra.id],
                    )
                ],
            )
        )
        service.registrar_precinto(
            envio["id"],
            PrecintoCreate(
                codigo="PREC-SERVICE-02",
                conservadora_id=conservadora.id,
                colocado_por="Personal de prueba",
            ),
        )
        anomalia = service.verificar_precinto(
            envio["id"],
            VerificacionPrecintoCreate(
                conservadora_id=conservadora.id,
                codigo_observado="PREC-SERVICE-02",
                resultado="roto",
                responsable="Personal de prueba",
            ),
        )
        assert anomalia["incidencias"][0].tipo == "precinto_roto"
        try:
            service.despachar_envio(
                envio["id"],
                DespachoCreate(
                    responsable_despacho="Responsable de prueba",
                    transportista="Transporte de prueba",
                ),
            )
        except HTTPException as exc:
            assert exc.status_code == 409
        else:
            raise AssertionError("El despacho no debe continuar con el último precinto reportado como roto")

        envio_actualizado = service.obtener_envio(envio["id"])
        assert envio_actualizado["estado"] == "en_preparacion"
    finally:
        db.close()


def test_rechazo_del_state_al_empaquetar_revierte_el_envio(datos_prueba):
    with TestingSessionLocal() as db:
        primera = _preparar_datos(db, datos_prueba, "EMPAQUE-01")
        segunda = _preparar_datos(db, datos_prueba, "EMPAQUE-02")
        segunda.reportar_inconveniente("Problema de identificación")
        db.commit()

        servicio = EnvioService(db)
        conservadora = servicio.registrar_conservadora(ConservadoraCreate(codigo="EMPAQUE"))
        payload = EnvioCreate(
            origen="Clínica de prueba",
            destino="Laboratorio externo",
            condiciones_empaquetado="Muestras protegidas",
            conservadoras=[ContenidoConservadoraCreate(
                conservadora_id=conservadora.id,
                muestra_ids=[primera.id, segunda.id],
            )],
        )

        with pytest.raises(HTTPException, match="No se puede empaquetar.*con_inconveniente") as error:
            servicio.crear_envio(payload)

        assert error.value.status_code == 409
        assert servicio.listar_envios() == []
        assert conservadora.disponible
        assert primera.estado == "lista_para_envio"
        assert primera.historial == []
        assert segunda.estado == "con_inconveniente"


def test_despacho_revierte_el_lote_si_una_muestra_no_esta_empaquetada(datos_prueba):
    with TestingSessionLocal() as db:
        muestras = [
            _preparar_datos(db, datos_prueba, "DESPACHO-01"),
            _preparar_datos(db, datos_prueba, "DESPACHO-02"),
        ]
        servicio = EnvioService(db)
        conservadora = servicio.registrar_conservadora(ConservadoraCreate(codigo="DESPACHO"))
        envio = servicio.crear_envio(EnvioCreate(
            origen="Clínica de prueba",
            destino="Laboratorio externo",
            condiciones_empaquetado="Muestras protegidas",
            conservadoras=[ContenidoConservadoraCreate(
                conservadora_id=conservadora.id,
                muestra_ids=[muestra.id for muestra in muestras],
            )],
        ))
        envio_id = envio["id"]
        servicio.registrar_precinto(envio_id, PrecintoCreate(
            codigo="PREC-DESPACHO",
            conservadora_id=conservadora.id,
            colocado_por="Personal de prueba",
        ))
        primera, segunda = envio["muestras"]
        segunda.reportar_inconveniente("Incidencia durante la preparación")
        segunda.marcar_lista_para_envio("Incidencia revisada")
        db.commit()

        with pytest.raises(HTTPException, match="No se puede despachar.*lista_para_envio") as error:
            servicio.despachar_envio(envio_id, DespachoCreate(
                responsable_despacho="Personal de prueba",
                transportista="Transporte de prueba",
            ))

        assert error.value.status_code == 409
        actualizado = servicio.obtener_envio(envio_id)
        assert actualizado["estado"] == "en_preparacion"
        assert actualizado["fecha_despacho"] is None
        assert actualizado["remito"] is None
        assert primera.estado == "empaquetada"
        assert [evento.estado_nuevo for evento in primera.historial] == ["empaquetada"]
        assert segunda.estado == "lista_para_envio"


@pytest.mark.parametrize("otra_condicion", [
    "Temperatura Ambiente (15° a 25°C)",
    "Congelada (-20°C)",
    "Refrigerada (2° a 6°C)",
])
def test_envio_exige_la_misma_condicion_por_conservadora(datos_prueba, otra_condicion):
    with TestingSessionLocal() as db:
        primera = _preparar_datos(db, datos_prueba, "RANGO-01", "Refrigerada (2° a 8°C)")
        equivalente = _preparar_datos(db, datos_prueba, "RANGO-02", " 2°C – 8°C ")
        distinta = _preparar_datos(db, datos_prueba, "RANGO-03", otra_condicion)
        servicio = EnvioService(db)
        conservadora = servicio.registrar_conservadora(ConservadoraCreate(codigo="RANGO-01"))
        otra_conservadora = servicio.registrar_conservadora(ConservadoraCreate(codigo="RANGO-02"))
        datos_envio = {
            "origen": "Clínica de prueba",
            "destino": "Laboratorio externo",
            "condiciones_empaquetado": "Muestras protegidas",
        }

        with pytest.raises(HTTPException, match="misma condición de conservación") as error:
            servicio.crear_envio(EnvioCreate(**datos_envio, conservadoras=[
                ContenidoConservadoraCreate(
                    conservadora_id=conservadora.id,
                    muestra_ids=[primera.id, equivalente.id, distinta.id],
                ),
            ]))
        assert error.value.status_code == 400
        assert conservadora.disponible
        assert all(muestra.estado == "lista_para_envio" for muestra in [primera, equivalente, distinta])
        assert servicio.listar_envios() == []

        envio = servicio.crear_envio(EnvioCreate(**datos_envio, conservadoras=[
            ContenidoConservadoraCreate(
                conservadora_id=conservadora.id, muestra_ids=[primera.id, equivalente.id],
            ),
            ContenidoConservadoraCreate(conservadora_id=otra_conservadora.id, muestra_ids=[distinta.id]),
        ]))
        assert {muestra.id for muestra in envio["muestras"]} == {primera.id, equivalente.id, distinta.id}
        assert all(muestra.estado == "empaquetada" for muestra in envio["muestras"])


@pytest.mark.parametrize(
    ("condicion", "validas", "invalida"),
    [
        ("Refrigerada (2° a 8°C)", [2, 8], 8.1),
        ("Temperatura Ambiente (15° a 25°C)", [15, 25], 14.9),
        ("Congelada (-20°C)", [-20, -20.1], -19.9),
        ("Congelada (menos de -20°C)", [-20, -20.1], -19.9),
        ("Congelada (-20°C o menos)", [-20, -20.1, -25], -19.9),
        ("Refrigerar a 4°C", [4], 4.1),
        ("Estándar a temperatura ambiente", [22], 4),
    ],
)
def test_temperatura_de_salida_debe_cumplir_la_condicion(datos_prueba, condicion, validas, invalida):
    with TestingSessionLocal() as db:
        muestra = _preparar_datos(db, datos_prueba, "TEMP-01", condicion)
        servicio = EnvioService(db)
        conservadora = servicio.registrar_conservadora(ConservadoraCreate(codigo="TEMP-01"))
        envio = servicio.crear_envio(EnvioCreate(
            origen="Clínica de prueba",
            destino="Laboratorio externo",
            condiciones_empaquetado="Muestras protegidas",
            conservadoras=[
                ContenidoConservadoraCreate(conservadora_id=conservadora.id, muestra_ids=[muestra.id]),
            ],
        ))
        medicion = RegistroTemperaturaCreate(
            conservadora_id=conservadora.id,
            temperatura_requerida_c=invalida,
            temperatura_medida_c=invalida,
            fecha_medicion=datetime.now(timezone.utc),
            responsable="Personal de prueba",
        )

        with pytest.raises(HTTPException, match="La temperatura de salida debe ser") as error:
            servicio.registrar_temperatura(envio["id"], medicion)
        assert error.value.status_code == 422
        assert servicio.obtener_envio(envio["id"])["registros_temperatura"] == []

        for temperatura in validas:
            lectura = medicion.model_copy(update={"temperatura_medida_c": temperatura})
            preparado = servicio.registrar_temperatura(envio["id"], lectura)
        assert [r.temperatura_medida_c for r in preparado["registros_temperatura"]] == validas
