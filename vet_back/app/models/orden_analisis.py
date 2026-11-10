from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Table, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.patient import Consulta, Veterinario

# Tabla asociativa para definir tipos de muestra compatibles con cada tipo de análisis (US-09)
tipo_analisis_tipos_muestra = Table(
    "tipo_analisis_tipos_muestra",
    Base.metadata,
    Column("tipo_analisis_id", Integer, ForeignKey("tipos_analisis.id"), primary_key=True),
    Column("tipo_muestra_id", Integer, ForeignKey("tipos_muestra.id"), primary_key=True),
)


class TipoAnalisis(Base):
    __tablename__ = "tipos_analisis"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nombre: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    activo: Mapped[bool] = mapped_column(default=True)

    detalles: Mapped[list["DetalleOrdenAnalisis"]] = relationship(back_populates="tipo_analisis")
    tipos_muestra_compatibles: Mapped[list["TipoMuestra"]] = relationship(
        secondary=tipo_analisis_tipos_muestra,
        lazy="selectin",
    )


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
    consulta: Mapped[Consulta] = relationship()
    veterinario: Mapped[Veterinario] = relationship()
    detalles: Mapped[list["DetalleOrdenAnalisis"]] = relationship(
        back_populates="orden", cascade="all, delete-orphan"
    )
    historial: Mapped[list["HistorialOrdenAnalisis"]] = relationship(
        back_populates="orden", cascade="all, delete-orphan", order_by="HistorialOrdenAnalisis.changed_at"
    )
    muestras: Mapped[list["Muestra"]] = relationship(
        back_populates="orden", cascade="all, delete-orphan"
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
    asociaciones_muestras: Mapped[list["AsociacionDetalleMuestra"]] = relationship(
        back_populates="detalle", cascade="all, delete-orphan"
    )

    @property
    def tiene_muestra(self) -> bool:
        return len(self.asociaciones_muestras) > 0


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


# --- Entidades de Muestras Biológicas ---

class TipoMuestra(Base):
    __tablename__ = "tipos_muestra"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nombre: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    condiciones_conservacion_default: Mapped[str | None] = mapped_column(String(200), nullable=True)
    activo: Mapped[bool] = mapped_column(default=True)

    muestras: Mapped[list["Muestra"]] = relationship(back_populates="tipo_muestra")


class Muestra(Base):
    __tablename__ = "muestras"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    codigo_etiqueta: Mapped[str] = mapped_column(String(60), unique=True, index=True)
    orden_id: Mapped[int] = mapped_column(ForeignKey("ordenes_analisis.id"), index=True)
    tipo_muestra_id: Mapped[int] = mapped_column(ForeignKey("tipos_muestra.id"), index=True)
    fecha_extraccion: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), index=True
    )
    responsable_extraccion: Mapped[str] = mapped_column(String(160))
    condiciones_conservacion: Mapped[str] = mapped_column(String(200))
    observaciones_calidad: Mapped[str | None] = mapped_column(Text, nullable=True)
    estado: Mapped[str] = mapped_column(String(30), default="extraida", index=True)

    orden: Mapped[OrdenAnalisis] = relationship(back_populates="muestras")
    tipo_muestra: Mapped[TipoMuestra] = relationship(back_populates="muestras")
    historial: Mapped[list["HistorialMuestra"]] = relationship(
        back_populates="muestra", cascade="all, delete-orphan", order_by="HistorialMuestra.changed_at"
    )
    asociaciones_detalles: Mapped[list["AsociacionDetalleMuestra"]] = relationship(
        back_populates="muestra", cascade="all, delete-orphan"
    )


class HistorialMuestra(Base):
    __tablename__ = "historial_muestras"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    muestra_id: Mapped[int] = mapped_column(ForeignKey("muestras.id"), index=True)
    estado_anterior: Mapped[str | None] = mapped_column(String(30), nullable=True)
    estado_nuevo: Mapped[str] = mapped_column(String(30))
    changed_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    motivo: Mapped[str | None] = mapped_column(String(500), nullable=True)
    responsable: Mapped[str | None] = mapped_column(String(160), nullable=True)

    muestra: Mapped[Muestra] = relationship(back_populates="historial")


# --- Entidad Asociativa Muchos-a-Muchos: Muestras y Análisis ---

class AsociacionDetalleMuestra(Base):
    __tablename__ = "asociaciones_detalle_muestra"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    detalle_id: Mapped[int] = mapped_column(ForeignKey("detalles_orden_analisis.id"), index=True)
    muestra_id: Mapped[int] = mapped_column(ForeignKey("muestras.id"), index=True)
    fecha_asociacion: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    observaciones: Mapped[str | None] = mapped_column(String(300), nullable=True)

    __table_args__ = (
        UniqueConstraint("detalle_id", "muestra_id", name="uq_detalle_muestra"),
    )

    detalle: Mapped[DetalleOrdenAnalisis] = relationship(back_populates="asociaciones_muestras")
    muestra: Mapped[Muestra] = relationship(back_populates="asociaciones_detalles")

