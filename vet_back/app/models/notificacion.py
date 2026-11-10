from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class NotificacionVeterinario(Base):
    __tablename__ = "notificaciones_veterinario"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    veterinario_id: Mapped[int] = mapped_column(ForeignKey("veterinarios.id"), index=True)
    muestra_id: Mapped[int] = mapped_column(ForeignKey("muestras.id"), index=True)
    estado_anterior: Mapped[str | None] = mapped_column(String(30), nullable=True)
    estado_nuevo: Mapped[str] = mapped_column(String(30))
    mensaje: Mapped[str] = mapped_column(String(300))
    motivo: Mapped[str | None] = mapped_column(Text, nullable=True)
    ocurrido_en: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    creada_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    leida_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
