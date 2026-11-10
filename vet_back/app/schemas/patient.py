from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class ModeloORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class CrearResponsable(BaseModel):
    document_number: str = Field(min_length=3, max_length=40)
    full_name: str = Field(min_length=2, max_length=160)
    phone: str = Field(min_length=3, max_length=40)
    email: str | None = Field(default=None, max_length=254)
    address: str | None = Field(default=None, max_length=240)


class ActualizarResponsable(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=160)
    phone: str | None = Field(default=None, min_length=3, max_length=40)
    email: str | None = Field(default=None, max_length=254)
    address: str | None = Field(default=None, max_length=240)


class LecturaResponsable(ModeloORM):
    id: int
    document_number: str
    full_name: str
    phone: str
    email: str | None
    address: str | None


class CrearVeterinario(BaseModel):
    full_name: str = Field(min_length=2, max_length=160)
    license_number: str = Field(min_length=3, max_length=60)
    specialty: str | None = Field(default=None, max_length=120)


class ActualizarVeterinario(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=160)
    specialty: str | None = Field(default=None, max_length=120)
    active: bool | None = None


class LecturaVeterinario(ModeloORM):
    id: int
    full_name: str
    license_number: str
    specialty: str | None
    active: bool


class LecturaNotificacionVeterinario(ModeloORM):
    id: int
    veterinario_id: int
    muestra_id: int
    estado_anterior: str | None
    estado_nuevo: str
    mensaje: str
    motivo: str | None
    ocurrido_en: datetime
    creada_en: datetime
    leida_en: datetime | None


class CrearMascota(BaseModel):
    responsible_id: int
    name: str = Field(min_length=1, max_length=100)
    species: str = Field(min_length=2, max_length=80)
    breed: str | None = Field(default=None, max_length=100)
    sex: str | None = Field(default=None, max_length=30)
    birth_date: date | None = None
    notes: str | None = None


class ActualizarMascota(BaseModel):
    responsible_id: int | None = None
    name: str | None = Field(default=None, min_length=1, max_length=100)
    species: str | None = Field(default=None, min_length=2, max_length=80)
    breed: str | None = Field(default=None, max_length=100)
    sex: str | None = Field(default=None, max_length=30)
    birth_date: date | None = None
    notes: str | None = None


class LecturaMascota(ModeloORM):
    id: int
    responsible_id: int
    name: str
    species: str
    breed: str | None
    sex: str | None
    birth_date: date | None
    notes: str | None


class LecturaHistorialResponsablesMascota(ModeloORM):
    id: int
    responsible_id: int
    changed_at: datetime


class CrearTurno(BaseModel):
    pet_id: int
    veterinarian_id: int
    scheduled_at: datetime
    duration_minutes: int = Field(default=30, ge=10, le=240)
    reason: str | None = Field(default=None, max_length=500)


class ActualizarTurno(BaseModel):
    pet_id: int | None = None
    veterinarian_id: int | None = None
    scheduled_at: datetime | None = None
    duration_minutes: int | None = Field(default=None, ge=10, le=240)
    reason: str | None = Field(default=None, max_length=500)


class ActualizacionEstadoTurno(BaseModel):
    status: str
    reason: str | None = Field(default=None, max_length=500)


class LecturaTurno(ModeloORM):
    id: int
    pet_id: int
    veterinarian_id: int
    scheduled_at: datetime
    duration_minutes: int
    status: str
    reason: str | None
    created_at: datetime


class LecturaHistorialTurno(ModeloORM):
    id: int
    event: str
    previous_scheduled_at: datetime | None
    new_scheduled_at: datetime | None
    previous_status: str | None
    new_status: str | None
    changed_at: datetime
    reason: str | None


class CrearConsulta(BaseModel):
    pet_id: int
    veterinarian_id: int
    appointment_id: int | None = None
    attended_at: datetime | None = None
    reason: str = Field(min_length=2, max_length=500)
    observations: str | None = None
    diagnosis: str | None = None
    treatment: str | None = None


class LecturaConsulta(ModeloORM):
    id: int
    pet_id: int
    veterinarian_id: int
    appointment_id: int | None
    attended_at: datetime
    reason: str
    observations: str | None
    diagnosis: str | None
    treatment: str | None
