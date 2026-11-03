from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.patient import (
    Appointment,
    AppointmentHistory,
    Consultation,
    Pet,
    PetResponsibleHistory,
    Responsible,
    Veterinarian,
)
from app.schemas.patient import (
    AppointmentCreate,
    AppointmentHistoryRead,
    AppointmentRead,
    AppointmentStatusUpdate,
    AppointmentUpdate,
    ConsultationCreate,
    ConsultationRead,
    PetCreate,
    PetRead,
    PetResponsibleHistoryRead,
    PetUpdate,
    ResponsibleCreate,
    ResponsibleRead,
    ResponsibleUpdate,
    VeterinarianCreate,
    VeterinarianRead,
    VeterinarianUpdate,
)

router = APIRouter(prefix="/api/v1", tags=["Pacientes y atención"])
APPOINTMENT_STATUSES = {"pendiente", "confirmado", "cancelado", "atendido", "ausente"}
FINAL_APPOINTMENT_STATUSES = {"cancelado", "atendido", "ausente"}


def _get_or_404(db: Session, model, entity_id: int, label: str):
    entity = db.get(model, entity_id)
    if entity is None:
        raise HTTPException(status_code=404, detail=f"{label} no encontrado")
    return entity


def _commit(db: Session):
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Ya existe un registro con ese identificador") from exc


def _ensure_no_overlap(db: Session, veterinarian_id: int, starts_at, duration: int, exclude_id: int | None = None):
    ends_at = starts_at + timedelta(minutes=duration)
    query = select(Appointment).where(
        Appointment.veterinarian_id == veterinarian_id,
        Appointment.status.notin_(FINAL_APPOINTMENT_STATUSES),
        Appointment.scheduled_at < ends_at,
    )
    if exclude_id is not None:
        query = query.where(Appointment.id != exclude_id)
    for current in db.scalars(query):
        current_end = current.scheduled_at + timedelta(minutes=current.duration_minutes)
        if current_end > starts_at:
            raise HTTPException(status_code=409, detail="El profesional ya tiene un turno superpuesto")


@router.post("/responsables", response_model=ResponsibleRead, status_code=status.HTTP_201_CREATED)
def create_responsible(payload: ResponsibleCreate, db: Session = Depends(get_db)):
    responsible = Responsible(**payload.model_dump())
    db.add(responsible)
    _commit(db)
    db.refresh(responsible)
    return responsible


@router.get("/responsables", response_model=list[ResponsibleRead])
def list_responsibles(search: str | None = None, db: Session = Depends(get_db)):
    query = select(Responsible).order_by(Responsible.full_name)
    if search:
        query = query.where(Responsible.full_name.ilike(f"%{search}%"))
    return db.scalars(query).all()


@router.get("/responsables/{responsible_id}", response_model=ResponsibleRead)
def get_responsible(responsible_id: int, db: Session = Depends(get_db)):
    return _get_or_404(db, Responsible, responsible_id, "Responsable")


@router.patch("/responsables/{responsible_id}", response_model=ResponsibleRead)
def update_responsible(responsible_id: int, payload: ResponsibleUpdate, db: Session = Depends(get_db)):
    responsible = _get_or_404(db, Responsible, responsible_id, "Responsable")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(responsible, field, value)
    _commit(db)
    db.refresh(responsible)
    return responsible


@router.post("/veterinarios", response_model=VeterinarianRead, status_code=status.HTTP_201_CREATED)
def create_veterinarian(payload: VeterinarianCreate, db: Session = Depends(get_db)):
    veterinarian = Veterinarian(**payload.model_dump())
    db.add(veterinarian)
    _commit(db)
    db.refresh(veterinarian)
    return veterinarian


@router.get("/veterinarios", response_model=list[VeterinarianRead])
def list_veterinarians(db: Session = Depends(get_db)):
    return db.scalars(select(Veterinarian).order_by(Veterinarian.full_name)).all()


@router.patch("/veterinarios/{veterinarian_id}", response_model=VeterinarianRead)
def update_veterinarian(veterinarian_id: int, payload: VeterinarianUpdate, db: Session = Depends(get_db)):
    veterinarian = _get_or_404(db, Veterinarian, veterinarian_id, "Veterinario")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(veterinarian, field, value)
    _commit(db)
    db.refresh(veterinarian)
    return veterinarian


@router.post("/mascotas", response_model=PetRead, status_code=status.HTTP_201_CREATED)
def create_pet(payload: PetCreate, db: Session = Depends(get_db)):
    _get_or_404(db, Responsible, payload.responsible_id, "Responsable")
    pet = Pet(**payload.model_dump())
    db.add(pet)
    db.flush()
    db.add(PetResponsibleHistory(pet_id=pet.id, responsible_id=pet.responsible_id))
    _commit(db)
    db.refresh(pet)
    return pet


@router.get("/mascotas", response_model=list[PetRead])
def list_pets(responsible_id: int | None = None, search: str | None = None, db: Session = Depends(get_db)):
    query = select(Pet).order_by(Pet.name)
    if responsible_id is not None:
        query = query.where(Pet.responsible_id == responsible_id)
    if search:
        query = query.where(Pet.name.ilike(f"%{search}%"))
    return db.scalars(query).all()


@router.get("/mascotas/{pet_id}", response_model=PetRead)
def get_pet(pet_id: int, db: Session = Depends(get_db)):
    return _get_or_404(db, Pet, pet_id, "Mascota")


@router.patch("/mascotas/{pet_id}", response_model=PetRead)
def update_pet(pet_id: int, payload: PetUpdate, db: Session = Depends(get_db)):
    pet = _get_or_404(db, Pet, pet_id, "Mascota")
    changes = payload.model_dump(exclude_unset=True)
    new_responsible_id = changes.get("responsible_id")
    if new_responsible_id is not None and new_responsible_id != pet.responsible_id:
        _get_or_404(db, Responsible, new_responsible_id, "Responsable")
        db.add(PetResponsibleHistory(pet_id=pet.id, responsible_id=new_responsible_id))
    for field, value in changes.items():
        setattr(pet, field, value)
    _commit(db)
    db.refresh(pet)
    return pet


@router.get("/mascotas/{pet_id}/responsables-historicos", response_model=list[PetResponsibleHistoryRead])
def pet_responsible_history(pet_id: int, db: Session = Depends(get_db)):
    _get_or_404(db, Pet, pet_id, "Mascota")
    return db.scalars(
        select(PetResponsibleHistory).where(PetResponsibleHistory.pet_id == pet_id).order_by(PetResponsibleHistory.changed_at)
    ).all()


@router.post("/turnos", response_model=AppointmentRead, status_code=status.HTTP_201_CREATED)
def create_appointment(payload: AppointmentCreate, db: Session = Depends(get_db)):
    _get_or_404(db, Pet, payload.pet_id, "Mascota")
    veterinarian = _get_or_404(db, Veterinarian, payload.veterinarian_id, "Veterinario")
    if not veterinarian.active:
        raise HTTPException(status_code=409, detail="El profesional no está activo")
    _ensure_no_overlap(db, payload.veterinarian_id, payload.scheduled_at, payload.duration_minutes)
    appointment = Appointment(**payload.model_dump())
    db.add(appointment)
    db.flush()
    db.add(AppointmentHistory(
        appointment_id=appointment.id,
        event="creado",
        new_scheduled_at=appointment.scheduled_at,
        new_status=appointment.status,
    ))
    _commit(db)
    db.refresh(appointment)
    return appointment


@router.get("/turnos", response_model=list[AppointmentRead])
def list_appointments(
    veterinarian_id: int | None = None,
    pet_id: int | None = None,
    from_date: datetime | None = Query(default=None),
    to_date: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
):
    query = select(Appointment).order_by(Appointment.scheduled_at)
    if veterinarian_id is not None:
        query = query.where(Appointment.veterinarian_id == veterinarian_id)
    if pet_id is not None:
        query = query.where(Appointment.pet_id == pet_id)
    if from_date is not None:
        query = query.where(Appointment.scheduled_at >= from_date)
    if to_date is not None:
        query = query.where(Appointment.scheduled_at <= to_date)
    return db.scalars(query).all()


@router.patch("/turnos/{appointment_id}", response_model=AppointmentRead)
def update_appointment(appointment_id: int, payload: AppointmentUpdate, db: Session = Depends(get_db)):
    appointment = _get_or_404(db, Appointment, appointment_id, "Turno")
    if appointment.status in FINAL_APPOINTMENT_STATUSES:
        raise HTTPException(status_code=409, detail="No se puede modificar un turno cerrado")
    changes = payload.model_dump(exclude_unset=True)
    pet_id = changes.get("pet_id", appointment.pet_id)
    vet_id = changes.get("veterinarian_id", appointment.veterinarian_id)
    start = changes.get("scheduled_at", appointment.scheduled_at)
    duration = changes.get("duration_minutes", appointment.duration_minutes)
    _get_or_404(db, Pet, pet_id, "Mascota")
    professional = _get_or_404(db, Veterinarian, vet_id, "Veterinario")
    if not professional.active:
        raise HTTPException(status_code=409, detail="El profesional no está activo")
    _ensure_no_overlap(db, vet_id, start, duration, appointment.id)
    if start != appointment.scheduled_at:
        db.add(AppointmentHistory(
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
    _commit(db)
    db.refresh(appointment)
    return appointment


@router.patch("/turnos/{appointment_id}/estado", response_model=AppointmentRead)
def update_appointment_status(appointment_id: int, payload: AppointmentStatusUpdate, db: Session = Depends(get_db)):
    if payload.status not in APPOINTMENT_STATUSES:
        raise HTTPException(status_code=422, detail="Estado inválido")
    appointment = _get_or_404(db, Appointment, appointment_id, "Turno")
    if appointment.status in FINAL_APPOINTMENT_STATUSES and payload.status != appointment.status:
        raise HTTPException(status_code=409, detail="Un turno cerrado no puede reabrirse ni cambiar de estado")
    previous_status = appointment.status
    appointment.status = payload.status
    db.add(AppointmentHistory(
        appointment_id=appointment.id,
        event="estado_cambiado",
        previous_scheduled_at=appointment.scheduled_at,
        new_scheduled_at=appointment.scheduled_at,
        previous_status=previous_status,
        new_status=payload.status,
        reason=payload.reason,
    ))
    _commit(db)
    db.refresh(appointment)
    return appointment


@router.get("/turnos/{appointment_id}/historial", response_model=list[AppointmentHistoryRead])
def appointment_history(appointment_id: int, db: Session = Depends(get_db)):
    _get_or_404(db, Appointment, appointment_id, "Turno")
    return db.scalars(
        select(AppointmentHistory)
        .where(AppointmentHistory.appointment_id == appointment_id)
        .order_by(AppointmentHistory.changed_at)
    ).all()


@router.post("/consultas", response_model=ConsultationRead, status_code=status.HTTP_201_CREATED)
def create_consultation(payload: ConsultationCreate, db: Session = Depends(get_db)):
    _get_or_404(db, Pet, payload.pet_id, "Mascota")
    _get_or_404(db, Veterinarian, payload.veterinarian_id, "Veterinario")
    if payload.appointment_id is not None:
        appointment = _get_or_404(db, Appointment, payload.appointment_id, "Turno")
        if appointment.pet_id != payload.pet_id or appointment.veterinarian_id != payload.veterinarian_id:
            raise HTTPException(status_code=422, detail="El turno debe corresponder a la mascota y profesional de la consulta")
        if appointment.status == "cancelado":
            raise HTTPException(status_code=409, detail="No se puede registrar una consulta sobre un turno cancelado")
        previous_status = appointment.status
        appointment.status = "atendido"
        if previous_status != "atendido":
            db.add(AppointmentHistory(
                appointment_id=appointment.id,
                event="estado_cambiado",
                previous_scheduled_at=appointment.scheduled_at,
                new_scheduled_at=appointment.scheduled_at,
                previous_status=previous_status,
                new_status="atendido",
            ))
    consultation = Consultation(**payload.model_dump(exclude_none=True))
    db.add(consultation)
    _commit(db)
    db.refresh(consultation)
    return consultation


@router.get("/consultas", response_model=list[ConsultationRead])
def list_consultations(pet_id: int | None = None, db: Session = Depends(get_db)):
    query = select(Consultation).order_by(Consultation.attended_at.desc())
    if pet_id is not None:
        query = query.where(Consultation.pet_id == pet_id)
    return db.scalars(query).all()


@router.get("/mascotas/{pet_id}/historia-clinica", response_model=list[ConsultationRead])
def pet_medical_history(pet_id: int, db: Session = Depends(get_db)):
    _get_or_404(db, Pet, pet_id, "Mascota")
    return db.scalars(
        select(Consultation).where(Consultation.pet_id == pet_id).order_by(Consultation.attended_at.desc())
    ).all()
