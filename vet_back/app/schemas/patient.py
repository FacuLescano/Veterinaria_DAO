from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ResponsibleCreate(BaseModel):
    document_number: str = Field(min_length=3, max_length=40)
    full_name: str = Field(min_length=2, max_length=160)
    phone: str = Field(min_length=3, max_length=40)
    email: str | None = Field(default=None, max_length=254)
    address: str | None = Field(default=None, max_length=240)


class ResponsibleUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=160)
    phone: str | None = Field(default=None, min_length=3, max_length=40)
    email: str | None = Field(default=None, max_length=254)
    address: str | None = Field(default=None, max_length=240)


class ResponsibleRead(ORMModel):
    id: int
    document_number: str
    full_name: str
    phone: str
    email: str | None
    address: str | None


class VeterinarianCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=160)
    license_number: str = Field(min_length=3, max_length=60)
    specialty: str | None = Field(default=None, max_length=120)


class VeterinarianUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=160)
    specialty: str | None = Field(default=None, max_length=120)
    active: bool | None = None


class VeterinarianRead(ORMModel):
    id: int
    full_name: str
    license_number: str
    specialty: str | None
    active: bool


class PetCreate(BaseModel):
    responsible_id: int
    name: str = Field(min_length=1, max_length=100)
    species: str = Field(min_length=2, max_length=80)
    breed: str | None = Field(default=None, max_length=100)
    sex: str | None = Field(default=None, max_length=30)
    birth_date: date | None = None
    notes: str | None = None


class PetUpdate(BaseModel):
    responsible_id: int | None = None
    name: str | None = Field(default=None, min_length=1, max_length=100)
    species: str | None = Field(default=None, min_length=2, max_length=80)
    breed: str | None = Field(default=None, max_length=100)
    sex: str | None = Field(default=None, max_length=30)
    birth_date: date | None = None
    notes: str | None = None


class PetRead(ORMModel):
    id: int
    responsible_id: int
    name: str
    species: str
    breed: str | None
    sex: str | None
    birth_date: date | None
    notes: str | None


class PetResponsibleHistoryRead(ORMModel):
    id: int
    responsible_id: int
    changed_at: datetime


class AppointmentCreate(BaseModel):
    pet_id: int
    veterinarian_id: int
    scheduled_at: datetime
    duration_minutes: int = Field(default=30, ge=10, le=240)
    reason: str | None = Field(default=None, max_length=500)


class AppointmentUpdate(BaseModel):
    pet_id: int | None = None
    veterinarian_id: int | None = None
    scheduled_at: datetime | None = None
    duration_minutes: int | None = Field(default=None, ge=10, le=240)
    reason: str | None = Field(default=None, max_length=500)


class AppointmentStatusUpdate(BaseModel):
    status: str
    reason: str | None = Field(default=None, max_length=500)


class AppointmentRead(ORMModel):
    id: int
    pet_id: int
    veterinarian_id: int
    scheduled_at: datetime
    duration_minutes: int
    status: str
    reason: str | None
    created_at: datetime


class AppointmentHistoryRead(ORMModel):
    id: int
    event: str
    previous_scheduled_at: datetime | None
    new_scheduled_at: datetime | None
    previous_status: str | None
    new_status: str | None
    changed_at: datetime
    reason: str | None


class ConsultationCreate(BaseModel):
    pet_id: int
    veterinarian_id: int
    appointment_id: int | None = None
    attended_at: datetime | None = None
    reason: str = Field(min_length=2, max_length=500)
    observations: str | None = None
    diagnosis: str | None = None
    treatment: str | None = None


class ConsultationRead(ORMModel):
    id: int
    pet_id: int
    veterinarian_id: int
    appointment_id: int | None
    attended_at: datetime
    reason: str
    observations: str | None
    diagnosis: str | None
    treatment: str | None
