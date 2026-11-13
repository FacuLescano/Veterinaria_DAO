from datetime import datetime, timezone

import pytest

from app.models.notificacion import NotificacionVeterinario
from app.models.envio import Conservadora, Envio, envio_muestras
from app.models.orden_analisis import DetalleOrdenAnalisis, Muestra, OrdenAnalisis
from app.models.paciente import Consulta, Mascota, Responsable, Veterinario
from app.models.recepcion import ResultadoAnalisis
from app.api.patients import listar_notificaciones
from app.observers.muestra import RecepcionMuestra, VeterinarioObserver
from app.observers.resultados import ResponsableMascotaObserver, ResultadosRegistrados, resultados_analisis
from app.schemas.recepcion import ResultadoEntrada, VerificacionPrecintoEntrada
from app.services import recepcion as servicio_recepcion
from test.conftest import TestingSessionLocal


@pytest.mark.parametrize("resultado", ["aceptada", "rechazada"])
def test_recepcion_persiste_aviso_para_el_veterinario_solicitante(datos_prueba, resultado):
    db = TestingSessionLocal()
    try:
        consulta = db.get(Consulta, datos_prueba["consulta_id"])
        solicitante_id = datos_prueba["veterinario_id"]
        otro = Veterinario(full_name="Dr. Otro", license_number=f"MP-OTRO-{resultado}", active=True)
        db.add(otro)
        db.flush()
        orden = OrdenAnalisis(consulta_id=consulta.id, veterinario_id=solicitante_id, estado="enviada")
        db.add(orden)
        db.flush()
        muestra = Muestra(
            codigo_etiqueta=f"M-{resultado}", orden_id=orden.id,
            tipo_muestra_id=datos_prueba["tipo_muestra_id"], responsable_extraccion="Dra. Lopez",
            condiciones_conservacion="Refrigerada", estado="enviada",
        )
        db.add(muestra)
        db.flush()
        VeterinarioObserver().actualizar_recepcion(RecepcionMuestra(
            muestra_id=muestra.id, codigo_etiqueta=muestra.codigo_etiqueta, orden_id=orden.id,
            veterinario_id=solicitante_id, mascota_nombre="Firulais", resultado=resultado,
            condicion_precinto="integro" if resultado == "aceptada" else "roto",
            ocurrido_en=datetime.now(timezone.utc), mensaje=f"Recepción {resultado} de Firulais",
        ), db)
        db.commit()
        avisos = db.query(NotificacionVeterinario).all()
        assert len(avisos) == 1
        assert avisos[0].veterinario_id == solicitante_id
        assert avisos[0].estado_nuevo == resultado
        assert otro.id != avisos[0].veterinario_id
        assert "Firulais" in avisos[0].mensaje
        assert avisos[0].motivo is not None
    finally:
        db.close()


@pytest.mark.parametrize("condicion,esperado", [("integro", "aceptada"), ("roto", "rechazada")])
def test_verificacion_precinto_publica_aviso_de_recepcion(datos_prueba, condicion, esperado):
    db = TestingSessionLocal()
    try:
        consulta = db.get(Consulta, datos_prueba["consulta_id"])
        orden = OrdenAnalisis(consulta_id=consulta.id, veterinario_id=datos_prueba["veterinario_id"], estado="enviada")
        db.add(orden)
        db.flush()
        muestra = Muestra(
            codigo_etiqueta=f"M-VERIFY-{condicion}", orden_id=orden.id,
            tipo_muestra_id=datos_prueba["tipo_muestra_id"], responsable_extraccion="Dra. Lopez",
            condiciones_conservacion="Refrigerada", estado="enviada",
        )
        conservadora = Conservadora(codigo=f"C-VERIFY-{condicion}", descripcion="Prueba", disponible=False)
        db.add_all([muestra, conservadora])
        db.flush()
        envio = Envio(
            origen="Clínica", destino="Laboratorio", condiciones_empaquetado="Refrigerado",
            estado="despachado",
        )
        db.add(envio)
        db.flush()
        db.execute(envio_muestras.insert().values(
            envio_id=envio.id, muestra_id=muestra.id, conservadora_id=conservadora.id
        ))
        db.commit()
        verificacion = VerificacionPrecintoEntrada(
            envio_id=str(envio.id), estado=condicion, fecha_verificacion=datetime.now(timezone.utc),
            responsable_id="Operador", codigo_esperado="PREC-1", codigo_observado="PREC-1" if condicion == "integro" else "ROTO",
        )
        servicio_recepcion.registrar_verificacion(db, verificacion)
        avisos = db.query(NotificacionVeterinario).filter(NotificacionVeterinario.muestra_id == muestra.id).all()
        assert len(avisos) == 1
        assert avisos[0].estado_nuevo == esperado
        assert avisos[0].veterinario_id == datos_prueba["veterinario_id"]
        assert avisos[0].muestra_id == muestra.id
        assert "precinto" in avisos[0].mensaje
        estado_muestra = "recibida" if esperado == "aceptada" else "rechazada"
        assert f"muestra {estado_muestra}" in avisos[0].mensaje
        db.add(NotificacionVeterinario(
            veterinario_id=datos_prueba["veterinario_id"], muestra_id=muestra.id,
            estado_nuevo="enviada", mensaje="Cambio de estado no relacionado con recepción",
            ocurrido_en=datetime.now(timezone.utc),
        ))
        db.commit()
        bandeja = listar_notificaciones(db=db)
        assert len(bandeja) == 1
        assert bandeja[0].estado_nuevo == esperado
    finally:
        db.close()


class CorreoSimulado:
    def __init__(self):
        self.envios = []

    def enviar_resultados_disponibles(self, destinatario, nombre_responsable, nombre_mascota):
        self.envios.append((destinatario, nombre_responsable, nombre_mascota))
        return True


def test_resultados_observer_delega_correo_al_servicio_simulado(datos_prueba):
    db = TestingSessionLocal()
    try:
        responsable = db.query(Responsable).filter_by(document_number="12345678").one()
        responsable.email = "responsable@example.test"
        db.commit()
        correo = CorreoSimulado()
        observer = ResponsableMascotaObserver(correo)
        mascota_id = db.query(Mascota.id).filter_by(responsible_id=responsable.id).scalar()
        observer.actualizar_resultados(ResultadosRegistrados("resultado-1", str(mascota_id)), db)
        assert correo.envios == [("responsable@example.test", "Juan Perez", "Firulais")]
    finally:
        db.close()


def test_registro_resultado_publica_una_vez_y_fallo_observer_no_revierte(datos_prueba, monkeypatch):
    db = TestingSessionLocal()
    try:
        consulta = db.get(Consulta, datos_prueba["consulta_id"])
        orden = OrdenAnalisis(consulta_id=consulta.id, veterinario_id=datos_prueba["veterinario_id"])
        db.add(orden)
        db.flush()
        detalle = DetalleOrdenAnalisis(orden_id=orden.id, tipo_analisis_id=datos_prueba["tipo_analisis_id"])
        db.add(detalle)
        db.commit()

        eventos = []
        def publicar(evento, sesion):
            eventos.append(evento)
            raise RuntimeError("fallo simulado de notificación")
        monkeypatch.setattr(resultados_analisis, "notificar", publicar)
        datos = ResultadoEntrada(
            orden_id=str(orden.id), detalle_orden_id=str(detalle.id), paciente_id=str(consulta.pet_id),
            fecha_recepcion=datetime.now(timezone.utc), procedencia="Laboratorio de prueba", datos={},
            informe_nombre="informe-unico.pdf", registrado_por="Operador",
        )
        creado = servicio_recepcion.registrar_resultado(db, datos)
        assert creado is not None
        assert len(eventos) == 1
        assert servicio_recepcion.registrar_resultado(db, datos) is None
        assert len(eventos) == 1
        assert db.get(ResultadoAnalisis, creado.id) is not None
    finally:
        db.close()
