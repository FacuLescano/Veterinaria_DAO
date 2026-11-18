from datetime import datetime, timezone

import pytest
from fastapi import HTTPException

from app.core.laboratorio_gateway import LaboratorioMock
from app.models.orden_analisis import AsociacionDetalleMuestra, DetalleOrdenAnalisis, Muestra, OrdenAnalisis, TipoAnalisis
from app.models.recepcion import ResultadoAnalisis
from app.observers.resultados import resultados_analisis
from app.services import recepcion
from test.conftest import TestingSessionLocal


def crear_muestra_recibida(db, datos_prueba, codigo="M-GATEWAY"):
    orden = OrdenAnalisis(consulta_id=datos_prueba["consulta_id"], veterinario_id=datos_prueba["veterinario_id"])
    renal = TipoAnalisis(nombre=f"Perfil Renal {codigo}", activo=True)
    db.add_all([orden, renal])
    db.flush()
    hemograma = DetalleOrdenAnalisis(orden_id=orden.id, tipo_analisis_id=datos_prueba["tipo_analisis_id"])
    perfil_renal = DetalleOrdenAnalisis(orden_id=orden.id, tipo_analisis_id=renal.id)
    db.add_all([hemograma, perfil_renal])
    muestra = Muestra(
        codigo_etiqueta=codigo, orden_id=orden.id, tipo_muestra_id=datos_prueba["tipo_muestra_id"],
        responsable_extraccion="Dra. Lopez", condiciones_conservacion="Refrigerada", estado="recibida",
    )
    db.add(muestra)
    db.flush()
    db.add_all([
        AsociacionDetalleMuestra(detalle_id=hemograma.id, muestra_id=muestra.id),
        AsociacionDetalleMuestra(detalle_id=perfil_renal.id, muestra_id=muestra.id),
    ])
    db.commit()
    return muestra.id, orden.id, [hemograma.id, perfil_renal.id]


def test_mock_ofrece_escenarios_deterministas_y_analisis_del_catalogo(datos_prueba):
    db = TestingSessionLocal()
    try:
        muestra_id, _, detalle_ids = crear_muestra_recibida(db, datos_prueba)
        muestra = db.get(Muestra, muestra_id)
        analisis = [{"detalle_id": str(a.detalle.id), "nombre": a.detalle.tipo_analisis.nombre} for a in muestra.asociaciones_detalles]
        gateway = LaboratorioMock()
        instante_antes = datetime.now(timezone.utc)
        primera = gateway.consultar_resultados(str(muestra_id), analisis, "multiples")
        segunda = gateway.consultar_resultados(str(muestra_id), analisis, "multiples")
        instante_despues = datetime.now(timezone.utc)
        completa = gateway.consultar_resultados(str(muestra_id), analisis, "completo")
        assert primera.resultados == segunda.resultados
        assert instante_antes <= primera.fecha_recepcion <= instante_despues
        assert instante_antes <= segunda.fecha_recepcion <= instante_despues
        assert len(completa.resultados) == len(analisis)
        assert completa.resultados[0].valores != primera.resultados[0].valores
        assert {r.detalle_id for r in primera.resultados} == {str(i) for i in detalle_ids}
        assert primera.resultados[0].valores != primera.resultados[1].valores
        assert gateway.consultar_resultados(str(muestra_id), analisis, "pendientes").estado == "pendiente"
        assert gateway.consultar_resultados(str(muestra_id), analisis, "sin_resultados").estado == "sin_resultados"
    finally:
        db.close()


def test_consulta_rechaza_respuesta_invalida_sin_persistir(datos_prueba):
    db = TestingSessionLocal()
    try:
        muestra_id, _, _ = crear_muestra_recibida(db, datos_prueba, "M-INVALID")
        with pytest.raises(HTTPException) as error:
            recepcion.recibir_resultados_laboratorio(db, str(muestra_id), escenario="invalido")
        assert error.value.status_code == 422
        assert db.query(ResultadoAnalisis).count() == 0
    finally:
        db.close()


def test_registro_persiste_resultados_cambia_estado_y_publica_un_evento(datos_prueba, monkeypatch):
    db = TestingSessionLocal()
    try:
        muestra_id, orden_id, detalle_ids = crear_muestra_recibida(db, datos_prueba, "M-REGISTER")
        eventos = []
        monkeypatch.setattr(resultados_analisis, "notificar", lambda evento, sesion: eventos.append(evento))
        respuesta = recepcion.recibir_resultados_laboratorio(db, str(muestra_id))
        db.expire_all()
        muestra = db.get(Muestra, muestra_id)
        orden = db.get(OrdenAnalisis, orden_id)
        guardados = db.query(ResultadoAnalisis).filter_by(muestra_id=str(muestra_id)).all()
        assert respuesta["estado"] == "registrado"
        assert len(guardados) == 2
        assert {int(r.detalle_orden_id) for r in guardados} == set(detalle_ids)
        assert muestra.estado == "analizada"
        assert orden.estado == "con_resultados"
        assert len(eventos) == 1
        assert eventos[0].paciente_id == str(orden.consulta.pet_id)
    finally:
        db.close()


@pytest.mark.parametrize("escenario,estado", [("pendientes", "pendiente"), ("sin_resultados", "sin_resultados")])
def test_respuestas_sin_resultados_no_persisten_ni_notifican(datos_prueba, monkeypatch, escenario, estado):
    db = TestingSessionLocal()
    try:
        muestra_id, _, _ = crear_muestra_recibida(db, datos_prueba, f"M-{escenario}")
        eventos = []
        monkeypatch.setattr(resultados_analisis, "notificar", lambda evento, sesion: eventos.append(evento))
        respuesta = recepcion.recibir_resultados_laboratorio(db, str(muestra_id), escenario=escenario)
        assert respuesta["estado"] == estado
        assert db.query(ResultadoAnalisis).count() == 0
        assert db.get(Muestra, muestra_id).estado == "recibida"
        assert eventos == []
    finally:
        db.close()


def test_reintento_no_duplica_resultados_ni_eventos(datos_prueba, monkeypatch):
    db = TestingSessionLocal()
    try:
        muestra_id, _, _ = crear_muestra_recibida(db, datos_prueba, "M-REPEAT")
        eventos = []
        monkeypatch.setattr(resultados_analisis, "notificar", lambda evento, sesion: eventos.append(evento))
        recepcion.recibir_resultados_laboratorio(db, str(muestra_id))
        with pytest.raises(HTTPException) as error:
            recepcion.recibir_resultados_laboratorio(db, str(muestra_id))
        assert error.value.status_code == 409
        assert db.query(ResultadoAnalisis).filter_by(muestra_id=str(muestra_id)).count() == 2
        assert len(eventos) == 1
    finally:
        db.close()


def test_no_sobrescribe_resultado_previamente_registrado(datos_prueba, monkeypatch):
    db = TestingSessionLocal()
    try:
        muestra_id, orden_id, detalle_ids = crear_muestra_recibida(db, datos_prueba, "M-EXISTING")
        orden = db.get(OrdenAnalisis, orden_id)
        previo = ResultadoAnalisis(
            orden_id=str(orden_id), detalle_orden_id=str(detalle_ids[0]), muestra_id=str(muestra_id),
            paciente_id=str(orden.consulta.pet_id), fecha_recepcion=datetime.now(timezone.utc),
            procedencia="Carga anterior", registrado_por="Veterinaria", datos={"valores": []},
        )
        db.add(previo)
        db.commit()
        eventos = []
        monkeypatch.setattr(resultados_analisis, "notificar", lambda evento, sesion: eventos.append(evento))
        with pytest.raises(HTTPException) as error:
            recepcion.recibir_resultados_laboratorio(db, str(muestra_id))
        assert error.value.status_code == 409
        assert db.query(ResultadoAnalisis).filter_by(orden_id=str(orden_id)).count() == 1
        assert eventos == []
    finally:
        db.close()
