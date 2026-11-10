from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


envio_muestras = Table(
    "envio_muestras",
    Base.metadata,
    Column("envio_id", Integer, ForeignKey("envios.id"), primary_key=True),
    Column("muestra_id", Integer, ForeignKey("muestras.id"), primary_key=True),
    Column("conservadora_id", Integer, ForeignKey("conservadoras.id"), nullable=False),
    UniqueConstraint("muestra_id", name="uq_muestra_un_envio"),
)

envio_conservadoras = Table(
    "envio_conservadoras",
    Base.metadata,
    Column("envio_id", Integer, ForeignKey("envios.id"), primary_key=True),
    Column("conservadora_id", Integer, ForeignKey("conservadoras.id"), primary_key=True),
)


class Conservadora(Base):
    __tablename__ = "conservadoras"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    codigo: Mapped[str] = mapped_column(String(60), unique=True, index=True)
    descripcion: Mapped[str | None] = mapped_column(String(300), nullable=True)
    disponible: Mapped[bool] = mapped_column(default=True, index=True)

    envios: Mapped[list["Envio"]] = relationship(
        "Envio", secondary=envio_conservadoras, back_populates="conservadoras"
    )
    precintos: Mapped[list["PrecintoSanitario"]] = relationship(back_populates="conservadora")


class Envio(Base):
    __tablename__ = "envios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    origen: Mapped[str] = mapped_column(String(160))
    destino: Mapped[str] = mapped_column(String(160))
    transportista: Mapped[str | None] = mapped_column(String(160), nullable=True)
    responsable_despacho: Mapped[str | None] = mapped_column(String(160), nullable=True)
    estado: Mapped[str] = mapped_column(String(30), default="en_preparacion", index=True)
    fecha_creacion: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), index=True
    )
    fecha_despacho: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    condiciones_empaquetado: Mapped[str] = mapped_column(String(500))
    observaciones: Mapped[str | None] = mapped_column(Text, nullable=True)

    muestras: Mapped[list["Muestra"]] = relationship(
        "Muestra", secondary=envio_muestras, back_populates="envio", lazy="selectin"
    )
    conservadoras: Mapped[list[Conservadora]] = relationship(
        secondary=envio_conservadoras, back_populates="envios", lazy="selectin"
    )
    precintos: Mapped[list["PrecintoSanitario"]] = relationship(
        back_populates="envio", cascade="all, delete-orphan", lazy="selectin"
    )
    verificaciones_precinto: Mapped[list["VerificacionPrecinto"]] = relationship(
        back_populates="envio", cascade="all, delete-orphan", order_by="VerificacionPrecinto.fecha_verificacion"
    )
    remito: Mapped["Remito | None"] = relationship(
        back_populates="envio", cascade="all, delete-orphan", uselist=False
    )
    historial: Mapped[list["HistorialEnvio"]] = relationship(
        back_populates="envio", cascade="all, delete-orphan", order_by="HistorialEnvio.fecha_evento"
    )
    registros_temperatura: Mapped[list["RegistroTemperatura"]] = relationship(
        back_populates="envio", cascade="all, delete-orphan"
    )
    incidencias: Mapped[list["IncidenciaTransporte"]] = relationship(
        back_populates="envio", cascade="all, delete-orphan"
    )


class PrecintoSanitario(Base):
    __tablename__ = "precintos_sanitarios"
    __table_args__ = (
        UniqueConstraint("envio_id", "conservadora_id", name="uq_precinto_conservadora_envio"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    codigo: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    envio_id: Mapped[int] = mapped_column(ForeignKey("envios.id"), index=True)
    conservadora_id: Mapped[int] = mapped_column(ForeignKey("conservadoras.id"), index=True)
    colocado_por: Mapped[str] = mapped_column(String(160))
    fecha_colocacion: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    estado: Mapped[str] = mapped_column(String(30), default="colocado")

    envio: Mapped[Envio] = relationship(back_populates="precintos")
    conservadora: Mapped[Conservadora] = relationship(back_populates="precintos")
    verificaciones: Mapped[list["VerificacionPrecinto"]] = relationship(
        back_populates="precinto", cascade="all, delete-orphan", order_by="VerificacionPrecinto.fecha_verificacion"
    )


class VerificacionPrecinto(Base):
    __tablename__ = "verificaciones_precinto"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    envio_id: Mapped[int] = mapped_column(ForeignKey("envios.id"), index=True)
    conservadora_id: Mapped[int] = mapped_column(ForeignKey("conservadoras.id"), index=True)
    precinto_id: Mapped[int | None] = mapped_column(
        ForeignKey("precintos_sanitarios.id"), nullable=True, index=True
    )
    codigo_observado: Mapped[str | None] = mapped_column(String(80), nullable=True)
    resultado: Mapped[str] = mapped_column(String(30))
    fecha_verificacion: Mapped[datetime] = mapped_column(DateTime, index=True)
    responsable: Mapped[str] = mapped_column(String(160))
    observaciones: Mapped[str | None] = mapped_column(Text, nullable=True)

    envio: Mapped[Envio] = relationship(back_populates="verificaciones_precinto")
    precinto: Mapped[PrecintoSanitario | None] = relationship(back_populates="verificaciones")


class Remito(Base):
    __tablename__ = "remitos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    numero: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    envio_id: Mapped[int] = mapped_column(ForeignKey("envios.id"), unique=True, index=True)
    fecha_emision: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    contenido_json: Mapped[str] = mapped_column(Text)

    envio: Mapped[Envio] = relationship(back_populates="remito")


class HistorialEnvio(Base):
    __tablename__ = "historial_envios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    envio_id: Mapped[int] = mapped_column(ForeignKey("envios.id"), index=True)
    estado_anterior: Mapped[str | None] = mapped_column(String(30), nullable=True)
    estado_nuevo: Mapped[str] = mapped_column(String(30))
    fecha_evento: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), index=True
    )
    responsable: Mapped[str] = mapped_column(String(160))
    observaciones: Mapped[str | None] = mapped_column(Text, nullable=True)

    envio: Mapped[Envio] = relationship(back_populates="historial")


class RegistroTemperatura(Base):
    __tablename__ = "registros_temperatura"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    envio_id: Mapped[int] = mapped_column(ForeignKey("envios.id"), index=True)
    conservadora_id: Mapped[int | None] = mapped_column(
        ForeignKey("conservadoras.id"), nullable=True, index=True
    )
    muestra_id: Mapped[int | None] = mapped_column(ForeignKey("muestras.id"), nullable=True, index=True)
    temperatura_requerida_c: Mapped[float | None] = mapped_column(Float, nullable=True)
    temperatura_medida_c: Mapped[float] = mapped_column(Float)
    unidad: Mapped[str] = mapped_column(String(12), default="°C")
    fecha_medicion: Mapped[datetime] = mapped_column(DateTime, index=True)
    responsable: Mapped[str] = mapped_column(String(160))
    dispositivo: Mapped[str | None] = mapped_column(String(160), nullable=True)
    observaciones: Mapped[str | None] = mapped_column(Text, nullable=True)

    envio: Mapped[Envio] = relationship(back_populates="registros_temperatura")


class IncidenciaTransporte(Base):
    __tablename__ = "incidencias_transporte"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    envio_id: Mapped[int] = mapped_column(ForeignKey("envios.id"), index=True)
    conservadora_id: Mapped[int | None] = mapped_column(
        ForeignKey("conservadoras.id"), nullable=True, index=True
    )
    muestra_id: Mapped[int | None] = mapped_column(ForeignKey("muestras.id"), nullable=True, index=True)
    tipo: Mapped[str] = mapped_column(String(80))
    descripcion: Mapped[str] = mapped_column(Text)
    fecha_evento: Mapped[datetime] = mapped_column(DateTime, index=True)
    responsable: Mapped[str] = mapped_column(String(160))

    envio: Mapped[Envio] = relationship(back_populates="incidencias")
