from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, Index, Integer, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Responsable(Base):
    __tablename__ = "responsables"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    document_number: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(160), index=True)
    phone: Mapped[str] = mapped_column(String(40))
    email: Mapped[str | None] = mapped_column(String(254), nullable=True)
    address: Mapped[str | None] = mapped_column(String(240), nullable=True)
    pets: Mapped[list["Mascota"]] = relationship(back_populates="responsible")


class Veterinario(Base):
    __tablename__ = "veterinarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    full_name: Mapped[str] = mapped_column(String(160), index=True)
    license_number: Mapped[str] = mapped_column(String(60), unique=True, index=True)
    specialty: Mapped[str | None] = mapped_column(String(120), nullable=True)
    active: Mapped[bool] = mapped_column(default=True)
    appointments: Mapped[list["Turno"]] = relationship(back_populates="veterinarian")
    consultations: Mapped[list["Consulta"]] = relationship(back_populates="veterinarian")


class Mascota(Base):
    __tablename__ = "mascotas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    responsible_id: Mapped[int] = mapped_column(ForeignKey("responsables.id"), index=True)
    name: Mapped[str] = mapped_column(String(100), index=True)
    species: Mapped[str] = mapped_column(String(80), index=True)
    breed: Mapped[str | None] = mapped_column(String(100), nullable=True)
    sex: Mapped[str | None] = mapped_column(String(30), nullable=True)
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    photo_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    responsible: Mapped[Responsable] = relationship(back_populates="pets")
    ownership_history: Mapped[list["HistorialResponsableMascota"]] = relationship(
        back_populates="pet", cascade="all, delete-orphan", order_by="HistorialResponsableMascota.changed_at"
    )
    appointments: Mapped[list["Turno"]] = relationship(back_populates="pet")
    consultations: Mapped[list["Consulta"]] = relationship(back_populates="pet")


class HistorialResponsableMascota(Base):
    __tablename__ = "historial_responsables_mascota"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pet_id: Mapped[int] = mapped_column(ForeignKey("mascotas.id"), index=True)
    responsible_id: Mapped[int] = mapped_column(ForeignKey("responsables.id"))
    changed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    pet: Mapped[Mascota] = relationship(back_populates="ownership_history")


class Turno(Base):
    __tablename__ = "turnos"
    __table_args__ = (
        Index(
            "uq_vet_turno_horario_activo",
            "veterinarian_id",
            "scheduled_at",
            unique=True,
            sqlite_where=text("status NOT IN ('cancelado', 'atendido', 'ausente')"),
            postgresql_where=text("status NOT IN ('cancelado', 'atendido', 'ausente')"),
        ),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    pet_id: Mapped[int] = mapped_column(ForeignKey("mascotas.id"), index=True)
    veterinarian_id: Mapped[int] = mapped_column(ForeignKey("veterinarios.id"), index=True)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    duration_minutes: Mapped[int] = mapped_column(default=30)
    status: Mapped[str] = mapped_column(String(20), default="pendiente", index=True)
    reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    pet: Mapped[Mascota] = relationship(back_populates="appointments")
    veterinarian: Mapped[Veterinario] = relationship(back_populates="appointments")
    consultations: Mapped[list["Consulta"]] = relationship(back_populates="appointment")
    history: Mapped[list["HistorialTurno"]] = relationship(
        back_populates="appointment", cascade="all, delete-orphan", order_by="HistorialTurno.changed_at"
    )


class HistorialTurno(Base):
    __tablename__ = "historial_turnos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    appointment_id: Mapped[int] = mapped_column(ForeignKey("turnos.id"), index=True)
    event: Mapped[str] = mapped_column(String(30))
    previous_scheduled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    new_scheduled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    previous_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    new_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    changed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    appointment: Mapped[Turno] = relationship(back_populates="history")


class Consulta(Base):
    __tablename__ = "consultas_medicas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    pet_id: Mapped[int] = mapped_column(ForeignKey("mascotas.id"), index=True)
    veterinarian_id: Mapped[int] = mapped_column(ForeignKey("veterinarios.id"), index=True)
    appointment_id: Mapped[int | None] = mapped_column(ForeignKey("turnos.id"), nullable=True, unique=True)
    attended_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    reason: Mapped[str] = mapped_column(String(500))
    observations: Mapped[str | None] = mapped_column(Text, nullable=True)
    diagnosis: Mapped[str | None] = mapped_column(Text, nullable=True)
    treatment: Mapped[str | None] = mapped_column(Text, nullable=True)
    pet: Mapped[Mascota] = relationship(back_populates="consultations")
    veterinarian: Mapped[Veterinario] = relationship(back_populates="consultations")
    appointment: Mapped[Turno | None] = relationship(back_populates="consultations")
