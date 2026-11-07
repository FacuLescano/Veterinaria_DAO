from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.patient import Consultation, Veterinarian


class TipoAnalisis(Base):
    __tablename__ = "tipos_analisis"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nombre: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    activo: Mapped[bool] = mapped_column(default=True)

    detalles: Mapped[list["DetalleOrdenAnalisis"]] = relationship(back_populates="tipo_analisis")


class OrdenAnalisis(Base):
    __tablename__ = "ordenes_analisis"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    consulta_id: Mapped[int] = mapped_column(ForeignKey("consultas_medicas.id"), index=True)
    veterinario_id: Mapped[int] = mapped_column(ForeignKey("veterinarios.id"), index=True)
    estado: Mapped[str] = mapped_column(String(30), default="solicitada", index=True)
    observaciones: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    # Relaciones de dominio
    consulta: Mapped[Consultation] = relationship()
    veterinario: Mapped[Veterinarian] = relationship()
    detalles: Mapped[list["DetalleOrdenAnalisis"]] = relationship(
        back_populates="orden", cascade="all, delete-orphan"
    )
    historial: Mapped[list["HistorialOrdenAnalisis"]] = relationship(
        back_populates="orden", cascade="all, delete-orphan", order_by="HistorialOrdenAnalisis.changed_at"
    )

    # Propiedades para facilitar la consulta del paciente y solicitante (US-07)
    @property
    def paciente_id(self) -> int | None:
        return self.consulta.pet_id if self.consulta else None

    @property
    def paciente_nombre(self) -> str | None:
        return self.consulta.pet.name if self.consulta and self.consulta.pet else None

    @property
    def veterinario_nombre(self) -> str | None:
        return self.veterinario.full_name if self.veterinario else None


class DetalleOrdenAnalisis(Base):
    __tablename__ = "detalles_orden_analisis"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    orden_id: Mapped[int] = mapped_column(ForeignKey("ordenes_analisis.id"), index=True)
    tipo_analisis_id: Mapped[int] = mapped_column(ForeignKey("tipos_analisis.id"), index=True)
    indicaciones: Mapped[str | None] = mapped_column(Text, nullable=True)
    estado: Mapped[str] = mapped_column(String(30), default="solicitado")

    orden: Mapped[OrdenAnalisis] = relationship(back_populates="detalles")
    tipo_analisis: Mapped[TipoAnalisis] = relationship(back_populates="detalles")


class HistorialOrdenAnalisis(Base):
    __tablename__ = "historial_ordenes_analisis"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    orden_id: Mapped[int] = mapped_column(ForeignKey("ordenes_analisis.id"), index=True)
    estado_anterior: Mapped[str | None] = mapped_column(String(30), nullable=True)
    estado_nuevo: Mapped[str] = mapped_column(String(30))
    changed_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    motivo: Mapped[str | None] = mapped_column(String(500), nullable=True)

    orden: Mapped[OrdenAnalisis] = relationship(back_populates="historial")
