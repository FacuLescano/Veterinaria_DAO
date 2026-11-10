from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from vet_back.app.db.recepcion import BaseModulo4


def ahora_utc():
    return datetime.now(timezone.utc)


class RecepcionEnvio(BaseModulo4):
    __tablename__ = "m4_recepciones_envio"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    envio_id: Mapped[str] = mapped_column(String(100), index=True)
    fecha_recepcion: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    responsable_id: Mapped[str] = mapped_column(String(100))
    estado: Mapped[str] = mapped_column(String(20))
    muestras_despachadas: Mapped[list] = mapped_column(JSON)
    muestras_recibidas: Mapped[list] = mapped_column(JSON)
    observaciones: Mapped[str | None] = mapped_column(Text, nullable=True)
    creada_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora_utc)
    incidencias: Mapped[list["Incidencia"]] = relationship(back_populates="recepcion")


class VerificacionPrecinto(BaseModulo4):
    __tablename__ = "m4_verificaciones_precinto"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    envio_id: Mapped[str] = mapped_column(String(100), index=True)
    precinto_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    codigo_esperado: Mapped[str | None] = mapped_column(String(100), nullable=True)
    codigo_observado: Mapped[str | None] = mapped_column(String(100), nullable=True)
    estado: Mapped[str] = mapped_column(String(20))
    fecha_verificacion: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    responsable_id: Mapped[str] = mapped_column(String(100))
    observaciones: Mapped[str | None] = mapped_column(Text, nullable=True)


class Incidencia(BaseModulo4):
    __tablename__ = "m4_incidencias"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    recepcion_id: Mapped[str | None] = mapped_column(ForeignKey("m4_recepciones_envio.id"), nullable=True)
    envio_id: Mapped[str] = mapped_column(String(100), index=True)
    tipo: Mapped[str] = mapped_column(String(40))
    descripcion: Mapped[str] = mapped_column(Text)
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    responsable_id: Mapped[str] = mapped_column(String(100))
    muestra_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    conservadora_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    precinto_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    resolucion: Mapped[str | None] = mapped_column(Text, nullable=True)
    responsable_resolucion_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    resuelta_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    recepcion: Mapped[RecepcionEnvio | None] = relationship(back_populates="incidencias")


class ResultadoAnalisis(BaseModulo4):
    __tablename__ = "m4_resultados_analisis"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    orden_id: Mapped[str] = mapped_column(String(100), index=True)
    detalle_orden_id: Mapped[str] = mapped_column(String(100), index=True)
    muestra_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    paciente_id: Mapped[str] = mapped_column(String(100), index=True)
    fecha_recepcion: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    procedencia: Mapped[str] = mapped_column(String(200))
    estado: Mapped[str] = mapped_column(String(20), default="recibido")
    datos: Mapped[dict] = mapped_column(JSON, default=dict)
    informe_uri: Mapped[str | None] = mapped_column(Text, nullable=True)
    informe_nombre: Mapped[str | None] = mapped_column(String(255), nullable=True)
    registrado_por: Mapped[str] = mapped_column(String(100))
    interpretacion_clinica: Mapped[str | None] = mapped_column(Text, nullable=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora_utc)
