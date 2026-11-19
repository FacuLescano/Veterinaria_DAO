"""Reglas de negocio para responsables, pacientes y atención clínica."""
from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.paciente import (
    Consulta, HistorialResponsableMascota, HistorialTurno, Mascota,
    Responsable, Turno, Veterinario,
)
from app.schemas.patient import (
    ActualizacionEstadoTurno, ActualizarMascota, ActualizarResponsable,
    ActualizarTurno, ActualizarVeterinario, CrearConsulta, CrearMascota,
    CrearResponsable, CrearTurno, CrearVeterinario,
)

APPOINTMENT_STATUSES = {"pendiente", "confirmado", "cancelado", "atendido", "ausente"}
FINAL_APPOINTMENT_STATUSES = {"cancelado", "atendido", "ausente"}
PAST_APPOINTMENT_DETAIL = "No se puede agendar un turno en una fecha u horario pasado."


class PatientService:
    def __init__(self, db: Session):
        self.db = db

    def _get(self, model, entity_id: int, label: str):
        entity = self.db.get(model, entity_id)
        if entity is None:
            raise HTTPException(status_code=404, detail=f"{label} no encontrado")
        return entity

    def _commit(self):
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise HTTPException(status_code=409, detail="Ya existe un registro con ese identificador") from exc

    def _commit_turno(self):
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise HTTPException(
                status_code=409,
                detail="El horario ya está ocupado para este profesional. Seleccioná otro horario.",
            ) from exc

    def _check_overlap(self, veterinarian_id: int, starts_at, duration: int, exclude_id: int | None = None):
        ends_at = starts_at + timedelta(minutes=duration)
        query = select(Turno).where(
            Turno.veterinarian_id == veterinarian_id,
            Turno.status.notin_(FINAL_APPOINTMENT_STATUSES),
            Turno.scheduled_at < ends_at,
        )
        if exclude_id is not None:
            query = query.where(Turno.id != exclude_id)
        for current in self.db.scalars(query):
            if current.scheduled_at + timedelta(minutes=current.duration_minutes) > starts_at:
                raise HTTPException(
                    status_code=409,
                    detail="El horario ya está ocupado para este profesional. Seleccioná otro horario.",
                )

    def _validar_horario_futuro(self, starts_at: datetime):
        ahora = datetime.now(starts_at.tzinfo) if starts_at.tzinfo is not None else datetime.now()
        if starts_at <= ahora:
            raise HTTPException(status_code=422, detail=PAST_APPOINTMENT_DETAIL)

    def crear_responsable(self, payload: CrearResponsable):
        entity = Responsable(**payload.model_dump()); self.db.add(entity); self._commit(); self.db.refresh(entity); return entity
    
    def listar_responsables(self, search: str | None = None):
        q = select(Responsable).order_by(Responsable.full_name)
        if search: q = q.where(Responsable.full_name.ilike(f"%{search}%"))
        return self.db.scalars(q).all()
    
    def obtener_responsable(self, entity_id: int): return self._get(Responsable, entity_id, "Responsable")

    def actualizar_responsable(self, entity_id: int, payload: ActualizarResponsable):
        entity = self.obtener_responsable(entity_id)
        for k, v in payload.model_dump(exclude_unset=True).items(): setattr(entity, k, v)
        self._commit(); self.db.refresh(entity); return entity

    def crear_veterinario(self, payload: CrearVeterinario):
        entity = Veterinario(**payload.model_dump()); self.db.add(entity); self._commit(); self.db.refresh(entity); return entity
    
    def listar_veterinarios(self): return self.db.scalars(select(Veterinario).order_by(Veterinario.full_name)).all()

    def actualizar_veterinario(self, entity_id: int, payload: ActualizarVeterinario):
        entity = self._get(Veterinario, entity_id, "Veterinario")
        for k, v in payload.model_dump(exclude_unset=True).items(): setattr(entity, k, v)
        self._commit(); self.db.refresh(entity); return entity

    def crear_mascota(self, payload: CrearMascota):
        self._get(Responsable, payload.responsible_id, "Responsable")
        entity = Mascota(**payload.model_dump()); self.db.add(entity); self.db.flush()
        self.db.add(HistorialResponsableMascota(pet_id=entity.id, responsible_id=entity.responsible_id))
        self._commit(); self.db.refresh(entity); return entity
    
    def listar_mascotas(self, responsible_id: int | None = None, search: str | None = None):
        q = select(Mascota).order_by(Mascota.name)
        if responsible_id is not None: q = q.where(Mascota.responsible_id == responsible_id)
        if search: q = q.where(Mascota.name.ilike(f"%{search}%"))
        return self.db.scalars(q).all()
    
    def obtener_mascota(self, entity_id: int): return self._get(Mascota, entity_id, "Mascota")

    def actualizar_mascota(self, entity_id: int, payload: ActualizarMascota):
        entity = self.obtener_mascota(entity_id); changes = payload.model_dump(exclude_unset=True)
        new_id = changes.get("responsible_id")
        if new_id is not None and new_id != entity.responsible_id:
            self._get(Responsable, new_id, "Responsable")
            self.db.add(HistorialResponsableMascota(pet_id=entity.id, responsible_id=new_id))
        for k, v in changes.items(): setattr(entity, k, v)
        self._commit(); self.db.refresh(entity); return entity
    
    def historial_responsables_mascota(self, pet_id: int):
        self.obtener_mascota(pet_id)
        return self.db.scalars(select(HistorialResponsableMascota).where(HistorialResponsableMascota.pet_id == pet_id).order_by(HistorialResponsableMascota.changed_at)).all()

    def crear_turno(self, payload: CrearTurno):
        self._get(Mascota, payload.pet_id, "Mascota"); vet = self._get(Veterinario, payload.veterinarian_id, "Veterinario")
        if not vet.active: raise HTTPException(status_code=409, detail="El profesional no está activo")
        self._validar_horario_futuro(payload.scheduled_at)
        self._check_overlap(payload.veterinarian_id, payload.scheduled_at, payload.duration_minutes)
        entity = Turno(**payload.model_dump()); self.db.add(entity); self.db.flush()
        self.db.add(HistorialTurno(appointment_id=entity.id, event="creado", new_scheduled_at=entity.scheduled_at, new_status=entity.status))
        self._commit_turno(); self.db.refresh(entity); return entity
    
    def listar_turnos(self, veterinarian_id=None, pet_id=None, from_date: datetime | None = None, to_date: datetime | None = None):
        q = select(Turno).order_by(Turno.scheduled_at)
        if veterinarian_id is not None: q = q.where(Turno.veterinarian_id == veterinarian_id)
        if pet_id is not None: q = q.where(Turno.pet_id == pet_id)
        if from_date is not None: q = q.where(Turno.scheduled_at >= from_date)
        if to_date is not None: q = q.where(Turno.scheduled_at <= to_date)
        return self.db.scalars(q).all()
    
    def actualizar_turno(self, appointment_id: int, payload: ActualizarTurno):
        entity = self._get(Turno, appointment_id, "Turno")
        if entity.status in FINAL_APPOINTMENT_STATUSES: raise HTTPException(status_code=409, detail="No se puede modificar un turno cerrado")
        changes = payload.model_dump(exclude_unset=True)
        pet_id = changes.get("pet_id", entity.pet_id); vet_id = changes.get("veterinarian_id", entity.veterinarian_id)
        start = changes.get("scheduled_at", entity.scheduled_at); duration = changes.get("duration_minutes", entity.duration_minutes)
        self._get(Mascota, pet_id, "Mascota"); vet = self._get(Veterinario, vet_id, "Veterinario")
        if not vet.active: raise HTTPException(status_code=409, detail="El profesional no está activo")
        if start != entity.scheduled_at:
            self._validar_horario_futuro(start)
        self._check_overlap(vet_id, start, duration, entity.id)
        if start != entity.scheduled_at:
            self.db.add(HistorialTurno(appointment_id=entity.id, event="reprogramado", previous_scheduled_at=entity.scheduled_at, new_scheduled_at=start, previous_status=entity.status, new_status=entity.status, reason=changes.get("reason")))
        for k, v in changes.items(): setattr(entity, k, v)
        self._commit_turno(); self.db.refresh(entity); return entity
    
    def actualizar_estado_turno(self, appointment_id: int, payload: ActualizacionEstadoTurno):
        if payload.status not in APPOINTMENT_STATUSES: raise HTTPException(status_code=422, detail="Estado inválido")
        entity = self._get(Turno, appointment_id, "Turno")
        if entity.status in FINAL_APPOINTMENT_STATUSES and payload.status != entity.status: raise HTTPException(status_code=409, detail="Un turno cerrado no puede reabrirse ni cambiar de estado")
        previous = entity.status; entity.status = payload.status
        self.db.add(HistorialTurno(appointment_id=entity.id, event="estado_cambiado", previous_scheduled_at=entity.scheduled_at, new_scheduled_at=entity.scheduled_at, previous_status=previous, new_status=payload.status, reason=payload.reason))
        self._commit(); self.db.refresh(entity); return entity
    
    def historial_turno(self, appointment_id: int):
        self._get(Turno, appointment_id, "Turno")
        return self.db.scalars(select(HistorialTurno).where(HistorialTurno.appointment_id == appointment_id).order_by(HistorialTurno.changed_at)).all()

    def crear_consulta(self, payload: CrearConsulta):
        self._get(Mascota, payload.pet_id, "Mascota"); self._get(Veterinario, payload.veterinarian_id, "Veterinario")
        appointment = None
        if payload.appointment_id is not None:
            appointment = self._get(Turno, payload.appointment_id, "Turno")
            if appointment.pet_id != payload.pet_id or appointment.veterinarian_id != payload.veterinarian_id:
                raise HTTPException(status_code=422, detail="El turno debe corresponder a la mascota y profesional de la consulta")
            if appointment.status == "cancelado": raise HTTPException(status_code=409, detail="No se puede registrar una consulta sobre un turno cancelado")
        entity = Consulta(**payload.model_dump(exclude_none=True)); self.db.add(entity)
        if appointment is not None:
            previous = appointment.status
            appointment.status = "atendido"
            if previous != "atendido":
                self.db.add(HistorialTurno(appointment_id=appointment.id, event="estado_cambiado", previous_scheduled_at=appointment.scheduled_at, new_scheduled_at=appointment.scheduled_at, previous_status=previous, new_status="atendido"))
        self._commit(); self.db.refresh(entity); return entity
    
    def listar_consultas(self, pet_id: int | None = None):
        q = select(Consulta).order_by(Consulta.attended_at.desc())
        if pet_id is not None: q = q.where(Consulta.pet_id == pet_id)
        return self.db.scalars(q).all()
    
    def historia_clinica_mascota(self, pet_id: int):
        self.obtener_mascota(pet_id)
        return self.db.scalars(select(Consulta).where(Consulta.pet_id == pet_id).order_by(Consulta.attended_at.desc())).all()
