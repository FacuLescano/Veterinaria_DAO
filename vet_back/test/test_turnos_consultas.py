from datetime import datetime

import pytest


def crear_turno(client, datos_prueba, scheduled_at="2030-05-10T10:00:00"):
    return client.post("/api/v1/turnos", json={
        "pet_id": 1,
        "veterinarian_id": datos_prueba["veterinario_id"],
        "scheduled_at": scheduled_at,
        "duration_minutes": 30,
        "reason": "Control",
    })


@pytest.mark.parametrize("scheduled_at", ["2030-05-09T10:00:00", "2030-05-10T10:00:00"])
def test_turno_rechaza_fecha_u_horario_pasado(client, datos_prueba, monkeypatch, scheduled_at):
    import app.services.patient_service as patient_service

    class FechaHoraFija(datetime):
        @classmethod
        def now(cls, tz=None):
            actual = cls(2030, 5, 10, 10, 30)
            return actual.replace(tzinfo=tz) if tz is not None else actual

    monkeypatch.setattr(patient_service, "datetime", FechaHoraFija)

    respuesta = crear_turno(client, datos_prueba, scheduled_at)

    assert respuesta.status_code == 422
    assert respuesta.json()["detail"] == "No se puede agendar un turno en una fecha u horario pasado."


def test_turno_actualiza_estado_solo_al_confirmar_consulta(client, datos_prueba):
    turno = crear_turno(client, datos_prueba)
    assert turno.status_code == 201
    turno_id = turno.json()["id"]

    respuesta = client.post("/api/v1/consultas", json={
        "pet_id": 1,
        "veterinarian_id": datos_prueba["veterinario_id"],
        "appointment_id": turno_id,
        "attended_at": "2030-05-10T10:00:00",
        "reason": "Control clínico",
    })
    assert respuesta.status_code == 201
    assert respuesta.json()["appointment_id"] == turno_id
    assert client.get("/api/v1/turnos").json()[0]["status"] == "atendido"

    # Una segunda consulta no puede romper la relación única ni dejar el turno a medias.
    duplicada = client.post("/api/v1/consultas", json={
        "pet_id": 1,
        "veterinarian_id": datos_prueba["veterinario_id"],
        "appointment_id": turno_id,
        "reason": "Consulta duplicada",
    })
    assert duplicada.status_code == 409
    assert client.get("/api/v1/turnos").json()[0]["status"] == "atendido"


def test_disponibilidad_rechaza_solapamientos_y_permite_reutilizar_cancelado(client, datos_prueba):
    primero = crear_turno(client, datos_prueba)
    assert primero.status_code == 201
    solapado = crear_turno(client, datos_prueba, "2030-05-10T10:15:00")
    assert solapado.status_code == 409
    assert "horario ya está ocupado" in solapado.json()["detail"]

    cancelado = client.patch(f"/api/v1/turnos/{primero.json()['id']}/estado", json={"status": "cancelado"})
    assert cancelado.status_code == 200
    reemplazo = crear_turno(client, datos_prueba)
    assert reemplazo.status_code == 201


def test_migracion_elimina_unico_legacy_y_conserva_turnos(monkeypatch):
    from sqlalchemy import MetaData, UniqueConstraint, create_engine, inspect, text
    import app.main as main

    engine_legacy = create_engine("sqlite://")
    metadata_legacy = MetaData()
    for tabla in main.Base.metadata.tables.values():
        tabla_legacy = tabla.to_metadata(
            metadata_legacy,
            name="turnos" if tabla.name == "turnos" else None,
        )
    tabla_legacy = metadata_legacy.tables["turnos"]
    tabla_legacy.append_constraint(UniqueConstraint(
        "veterinarian_id", "scheduled_at", name="uq_vet_turno_horario"
    ))
    metadata_legacy.create_all(engine_legacy)
    with engine_legacy.begin() as connection:
        connection.execute(text(
            "INSERT INTO turnos (id, pet_id, veterinarian_id, scheduled_at, duration_minutes, status, created_at) "
            "VALUES (1, 1, 1, '2030-05-10 10:00:00', 30, 'cancelado', '2030-01-01 00:00:00')"
        ))
    monkeypatch.setattr(main, "engine", engine_legacy)

    main._migrar_indice_horario_turno()

    assert not any(
        c.get("name") == "uq_vet_turno_horario"
        for c in inspect(engine_legacy).get_unique_constraints("turnos")
    )
    with engine_legacy.connect() as connection:
        assert connection.execute(text("SELECT status FROM turnos WHERE id = 1")).scalar_one() == "cancelado"
    engine_legacy.dispose()

