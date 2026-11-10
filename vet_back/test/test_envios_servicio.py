from datetime import datetime, timezone

from fastapi import HTTPException

from app.models.envio import Conservadora
from app.models.orden_analisis import (
    AsociacionDetalleMuestra,
    DetalleOrdenAnalisis,
    Muestra,
    OrdenAnalisis,
)
from app.models.patient import Consulta
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


def _preparar_datos(db, datos_prueba, sufijo):
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
        condiciones_conservacion="Refrigerar a 4°C",
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
        muestra = _preparar_datos(db, datos_prueba, "SERVICE-01")
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
        service.registrar_precinto(
            envio["id"],
            PrecintoCreate(
                codigo="PREC-SERVICE-01",
                conservadora_id=conservadora.id,
                colocado_por="Personal de prueba",
            ),
        )
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
        assert "Bolsa biosegura" in despacho["remito"]["contenido"]["condiciones_empaquetado"]
        html = service.obtener_remito_html(envio["id"])
        assert "Imprimir remito" in html
        assert "PREC-SERVICE-01" in html

        medicion = service.registrar_temperatura(
            envio["id"],
            RegistroTemperaturaCreate(
                conservadora_id=conservadora.id,
                muestra_id=muestra.id,
                temperatura_requerida_c=4,
                temperatura_medida_c=4.2,
                fecha_medicion=datetime.now(timezone.utc),
                responsable="Transportista",
                unidad="°C",
            ),
        )
        assert medicion["registros_temperatura"][0].temperatura_requerida_c == 4
        assert medicion["registros_temperatura"][0].temperatura_medida_c == 4.2
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
