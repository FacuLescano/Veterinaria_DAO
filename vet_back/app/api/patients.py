from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import obtener_sesion_bd
from app.models.patient import (
    Turno,
    HistorialTurno,
    Consulta,
    Mascota,
    HistorialResponsableMascota,
    Responsable,
    Veterinario,
)
from app.schemas.patient import (
    CrearTurno,
    LecturaHistorialTurno,
    LecturaTurno,
    ActualizacionEstadoTurno,
    ActualizarTurno,
    CrearConsulta,
    LecturaConsulta,
    CrearMascota,
    LecturaMascota,
    LecturaHistorialResponsablesMascota,
    ActualizarMascota,
    CrearResponsable,
    LecturaResponsable,
    ActualizarResponsable,
    CrearVeterinario,
    LecturaVeterinario,
    ActualizarVeterinario,
)

router = APIRouter(prefix="/api/v1", tags=["Pacientes y atención"])
APPOINTMENT_STATUSES = {"pendiente", "confirmado", "cancelado", "atendido", "ausente"}
FINAL_APPOINTMENT_STATUSES = {"cancelado", "atendido", "ausente"}


def _obtener_o_404(db: Session, model, entity_id: int, etiqueta: str):
    entity = db.get(model, entity_id)
    if entity is None:
        raise HTTPException(status_code=404, detail=f"{etiqueta} no encontrado")
    return entity


def _confirmar_cambios(db: Session):
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Ya existe un registro con ese identificador") from exc


def _verificar_sin_superposicion(db: Session, veterinarian_id: int, starts_at, duration: int, exclude_id: int | None = None):
    ends_at = starts_at + timedelta(minutes=duration)
    query = select(Turno).where(
        Turno.veterinarian_id == veterinarian_id,
        Turno.status.notin_(FINAL_APPOINTMENT_STATUSES),
        Turno.scheduled_at < ends_at,
    )
    if exclude_id is not None:
        query = query.where(Turno.id != exclude_id)
    for current in db.scalars(query):
        current_end = current.scheduled_at + timedelta(minutes=current.duration_minutes)
        if current_end > starts_at:
            raise HTTPException(status_code=409, detail="El profesional ya tiene un turno superpuesto")


@router.post("/responsables", response_model=LecturaResponsable, status_code=status.HTTP_201_CREATED)
def crear_responsable(payload: CrearResponsable, db: Session = Depends(obtener_sesion_bd)):
    responsible = Responsable(**payload.model_dump())
    db.add(responsible)
    _confirmar_cambios(db)
    db.refresh(responsible)
    return responsible


@router.get("/responsables", response_model=list[LecturaResponsable])
def listar_responsables(search: str | None = None, db: Session = Depends(obtener_sesion_bd)):
    query = select(Responsable).order_by(Responsable.full_name)
    if search:
        query = query.where(Responsable.full_name.ilike(f"%{search}%"))
    return db.scalars(query).all()


@router.get("/responsables/{responsible_id}", response_model=LecturaResponsable)
def obtener_responsable(responsible_id: int, db: Session = Depends(obtener_sesion_bd)):
    return _obtener_o_404(db, Responsable, responsible_id, "Responsable")


@router.patch("/responsables/{responsible_id}", response_model=LecturaResponsable)
def actualizar_responsable(responsible_id: int, payload: ActualizarResponsable, db: Session = Depends(obtener_sesion_bd)):
    responsible = _obtener_o_404(db, Responsable, responsible_id, "Responsable")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(responsible, field, value)
    _confirmar_cambios(db)
    db.refresh(responsible)
    return responsible


@router.post("/veterinarios", response_model=LecturaVeterinario, status_code=status.HTTP_201_CREATED)
def crear_veterinario(payload: CrearVeterinario, db: Session = Depends(obtener_sesion_bd)):
    veterinarian = Veterinario(**payload.model_dump())
    db.add(veterinarian)
    _confirmar_cambios(db)
    db.refresh(veterinarian)
    return veterinarian


@router.get("/veterinarios", response_model=list[LecturaVeterinario])
def listar_veterinarios(db: Session = Depends(obtener_sesion_bd)):
    return db.scalars(select(Veterinario).order_by(Veterinario.full_name)).all()


@router.patch("/veterinarios/{veterinarian_id}", response_model=LecturaVeterinario)
def actualizar_veterinario(veterinarian_id: int, payload: ActualizarVeterinario, db: Session = Depends(obtener_sesion_bd)):
    veterinarian = _obtener_o_404(db, Veterinario, veterinarian_id, "Veterinario")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(veterinarian, field, value)
    _confirmar_cambios(db)
    db.refresh(veterinarian)
    return veterinarian


@router.post("/mascotas", response_model=LecturaMascota, status_code=status.HTTP_201_CREATED)
def crear_mascota(payload: CrearMascota, db: Session = Depends(obtener_sesion_bd)):
    _obtener_o_404(db, Responsable, payload.responsible_id, "Responsable")
    pet = Mascota(**payload.model_dump())
    db.add(pet)
    db.flush()
    db.add(HistorialResponsableMascota(pet_id=pet.id, responsible_id=pet.responsible_id))
    _confirmar_cambios(db)
    db.refresh(pet)
    return pet


@router.get("/mascotas", response_model=list[LecturaMascota])
def listar_mascotas(responsible_id: int | None = None, search: str | None = None, db: Session = Depends(obtener_sesion_bd)):
    query = select(Mascota).order_by(Mascota.name)
    if responsible_id is not None:
        query = query.where(Mascota.responsible_id == responsible_id)
    if search:
        query = query.where(Mascota.name.ilike(f"%{search}%"))
    return db.scalars(query).all()


@router.get("/mascotas/{pet_id}", response_model=LecturaMascota)
def obtener_mascota(pet_id: int, db: Session = Depends(obtener_sesion_bd)):
    return _obtener_o_404(db, Mascota, pet_id, "Mascota")


@router.patch("/mascotas/{pet_id}", response_model=LecturaMascota)
def actualizar_mascota(pet_id: int, payload: ActualizarMascota, db: Session = Depends(obtener_sesion_bd)):
    pet = _obtener_o_404(db, Mascota, pet_id, "Mascota")
    changes = payload.model_dump(exclude_unset=True)
    new_responsible_id = changes.get("responsible_id")
    if new_responsible_id is not None and new_responsible_id != pet.responsible_id:
        _obtener_o_404(db, Responsable, new_responsible_id, "Responsable")
        db.add(HistorialResponsableMascota(pet_id=pet.id, responsible_id=new_responsible_id))
    for field, value in changes.items():
        setattr(pet, field, value)
    _confirmar_cambios(db)
    db.refresh(pet)
    return pet


@router.get("/mascotas/{pet_id}/responsables-historicos", response_model=list[LecturaHistorialResponsablesMascota])
def historial_responsables_mascota(pet_id: int, db: Session = Depends(obtener_sesion_bd)):
    _obtener_o_404(db, Mascota, pet_id, "Mascota")
    return db.scalars(
        select(HistorialResponsableMascota).where(HistorialResponsableMascota.pet_id == pet_id).order_by(HistorialResponsableMascota.changed_at)
    ).all()


@router.post("/turnos", response_model=LecturaTurno, status_code=status.HTTP_201_CREATED)
def crear_turno(payload: CrearTurno, db: Session = Depends(obtener_sesion_bd)):
    _obtener_o_404(db, Mascota, payload.pet_id, "Mascota")
    veterinarian = _obtener_o_404(db, Veterinario, payload.veterinarian_id, "Veterinario")
    if not veterinarian.active:
        raise HTTPException(status_code=409, detail="El profesional no está activo")
    _verificar_sin_superposicion(db, payload.veterinarian_id, payload.scheduled_at, payload.duration_minutes)
    appointment = Turno(**payload.model_dump())
    db.add(appointment)
    db.flush()
    db.add(HistorialTurno(
        appointment_id=appointment.id,
        event="creado",
        new_scheduled_at=appointment.scheduled_at,
        new_status=appointment.status,
    ))
    _confirmar_cambios(db)
    db.refresh(appointment)
    return appointment


@router.get("/turnos", response_model=list[LecturaTurno])
def listar_turnos(
    veterinarian_id: int | None = None,
    pet_id: int | None = None,
    from_date: datetime | None = Query(default=None),
    to_date: datetime | None = Query(default=None),
    db: Session = Depends(obtener_sesion_bd),
):
    query = select(Turno).order_by(Turno.scheduled_at)
    if veterinarian_id is not None:
        query = query.where(Turno.veterinarian_id == veterinarian_id)
    if pet_id is not None:
        query = query.where(Turno.pet_id == pet_id)
    if from_date is not None:
        query = query.where(Turno.scheduled_at >= from_date)
    if to_date is not None:
        query = query.where(Turno.scheduled_at <= to_date)
    return db.scalars(query).all()


@router.patch("/turnos/{appointment_id}", response_model=LecturaTurno)
def actualizar_turno(appointment_id: int, payload: ActualizarTurno, db: Session = Depends(obtener_sesion_bd)):
    appointment = _obtener_o_404(db, Turno, appointment_id, "Turno")
    if appointment.status in FINAL_APPOINTMENT_STATUSES:
        raise HTTPException(status_code=409, detail="No se puede modificar un turno cerrado")
    changes = payload.model_dump(exclude_unset=True)
    pet_id = changes.get("pet_id", appointment.pet_id)
    vet_id = changes.get("veterinarian_id", appointment.veterinarian_id)
    start = changes.get("scheduled_at", appointment.scheduled_at)
    duration = changes.get("duration_minutes", appointment.duration_minutes)
    _obtener_o_404(db, Mascota, pet_id, "Mascota")
    professional = _obtener_o_404(db, Veterinario, vet_id, "Veterinario")
    if not professional.active:
        raise HTTPException(status_code=409, detail="El profesional no está activo")
    _verificar_sin_superposicion(db, vet_id, start, duration, appointment.id)
    if start != appointment.scheduled_at:
        db.add(HistorialTurno(
            appointment_id=appointment.id,
            event="reprogramado",
            previous_scheduled_at=appointment.scheduled_at,
            new_scheduled_at=start,
            previous_status=appointment.status,
            new_status=appointment.status,
            reason=changes.get("reason"),
        ))
    for field, value in changes.items():
        setattr(appointment, field, value)
    _confirmar_cambios(db)
    db.refresh(appointment)
    return appointment


@router.patch("/turnos/{appointment_id}/estado", response_model=LecturaTurno)
def actualizar_estado_turno(appointment_id: int, payload: ActualizacionEstadoTurno, db: Session = Depends(obtener_sesion_bd)):
    if payload.status not in APPOINTMENT_STATUSES:
        raise HTTPException(status_code=422, detail="Estado inválido")
    appointment = _obtener_o_404(db, Turno, appointment_id, "Turno")
    if appointment.status in FINAL_APPOINTMENT_STATUSES and payload.status != appointment.status:
        raise HTTPException(status_code=409, detail="Un turno cerrado no puede reabrirse ni cambiar de estado")
    previous_status = appointment.status
    appointment.status = payload.status
    db.add(HistorialTurno(
        appointment_id=appointment.id,
        event="estado_cambiado",
        previous_scheduled_at=appointment.scheduled_at,
        new_scheduled_at=appointment.scheduled_at,
        previous_status=previous_status,
        new_status=payload.status,
        reason=payload.reason,
    ))
    _confirmar_cambios(db)
    db.refresh(appointment)
    return appointment


@router.get("/turnos/{appointment_id}/historial", response_model=list[LecturaHistorialTurno])
def historial_turno(appointment_id: int, db: Session = Depends(obtener_sesion_bd)):
    _obtener_o_404(db, Turno, appointment_id, "Turno")
    return db.scalars(
        select(HistorialTurno)
        .where(HistorialTurno.appointment_id == appointment_id)
        .order_by(HistorialTurno.changed_at)
    ).all()


@router.post("/consultas", response_model=LecturaConsulta, status_code=status.HTTP_201_CREATED)
def crear_consulta(payload: CrearConsulta, db: Session = Depends(obtener_sesion_bd)):
    _obtener_o_404(db, Mascota, payload.pet_id, "Mascota")
    _obtener_o_404(db, Veterinario, payload.veterinarian_id, "Veterinario")
    if payload.appointment_id is not None:
        appointment = _obtener_o_404(db, Turno, payload.appointment_id, "Turno")
        if appointment.pet_id != payload.pet_id or appointment.veterinarian_id != payload.veterinarian_id:
            raise HTTPException(status_code=422, detail="El turno debe corresponder a la mascota y profesional de la consulta")
        if appointment.status == "cancelado":
            raise HTTPException(status_code=409, detail="No se puede registrar una consulta sobre un turno cancelado")
        previous_status = appointment.status
        appointment.status = "atendido"
        if previous_status != "atendido":
            db.add(HistorialTurno(
                appointment_id=appointment.id,
                event="estado_cambiado",
                previous_scheduled_at=appointment.scheduled_at,
                new_scheduled_at=appointment.scheduled_at,
                previous_status=previous_status,
                new_status="atendido",
            ))
    consultation = Consulta(**payload.model_dump(exclude_none=True))
    db.add(consultation)
    _confirmar_cambios(db)
    db.refresh(consultation)
    return consultation


@router.get("/consultas", response_model=list[LecturaConsulta])
def listar_consultas(pet_id: int | None = None, db: Session = Depends(obtener_sesion_bd)):
    query = select(Consulta).order_by(Consulta.attended_at.desc())
    if pet_id is not None:
        query = query.where(Consulta.pet_id == pet_id)
    return db.scalars(query).all()


@router.get("/mascotas/{pet_id}/historia-clinica", response_model=list[LecturaConsulta])
def historia_clinica_mascota(pet_id: int, db: Session = Depends(obtener_sesion_bd)):
    _obtener_o_404(db, Mascota, pet_id, "Mascota")
    return db.scalars(
        select(Consulta).where(Consulta.pet_id == pet_id).order_by(Consulta.attended_at.desc())
    ).all()
