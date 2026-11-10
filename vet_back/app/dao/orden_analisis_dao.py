from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.orden_analisis import (
    DetalleOrdenAnalisis,
    HistorialOrdenAnalisis,
    Muestra,
    OrdenAnalisis,
)
try:
    from app.models.patient import Consulta
except ImportError:
    from app.models.patient import Consultation as Consulta


class OrdenAnalisisDAO:
    """DAO para operaciones de persistencia relacionadas a OrdenAnalisis, sus detalles e historial (US-06 y US-07)."""

    def __init__(self, db: Session):
        self.db = db

    def _default_options(self):
        return [
            selectinload(OrdenAnalisis.detalles).selectinload(DetalleOrdenAnalisis.tipo_analisis),
            selectinload(OrdenAnalisis.detalles).selectinload(DetalleOrdenAnalisis.asociaciones_muestras),
            selectinload(OrdenAnalisis.muestras).selectinload(Muestra.tipo_muestra),
            selectinload(OrdenAnalisis.muestras).selectinload(Muestra.historial),
            selectinload(OrdenAnalisis.consulta).selectinload(Consulta.pet),
            selectinload(OrdenAnalisis.veterinario),
            selectinload(OrdenAnalisis.historial),
        ]

    def get_by_id(self, orden_id: int) -> OrdenAnalisis | None:
        query = (
            select(OrdenAnalisis)
            .where(OrdenAnalisis.id == orden_id)
            .options(*self._default_options())
        )
        return self.db.scalars(query).first()

    def get_detalle_by_id(self, detalle_id: int) -> DetalleOrdenAnalisis | None:
        query = (
            select(DetalleOrdenAnalisis)
            .where(DetalleOrdenAnalisis.id == detalle_id)
            .options(
                selectinload(DetalleOrdenAnalisis.tipo_analisis),
                selectinload(DetalleOrdenAnalisis.asociaciones_muestras),
            )
        )
        return self.db.scalars(query).first()

    def list_by_consulta_id(self, consulta_id: int) -> list[OrdenAnalisis]:
        query = (
            select(OrdenAnalisis)
            .where(OrdenAnalisis.consulta_id == consulta_id)
            .options(*self._default_options())
            .order_by(OrdenAnalisis.created_at.desc())
        )
        return list(self.db.scalars(query).all())

    def list_all(self) -> list[OrdenAnalisis]:
        query = (
            select(OrdenAnalisis)
            .options(*self._default_options())
            .order_by(OrdenAnalisis.created_at.desc())
        )
        return list(self.db.scalars(query).all())

    def create(self, orden: OrdenAnalisis) -> OrdenAnalisis:
        self.db.add(orden)
        self.db.flush()
        return orden

    def add_historial(self, historial: HistorialOrdenAnalisis) -> HistorialOrdenAnalisis:
        self.db.add(historial)
        self.db.flush()
        return historial

    def get_historial(self, orden_id: int) -> list[HistorialOrdenAnalisis]:
        query = (
            select(HistorialOrdenAnalisis)
            .where(HistorialOrdenAnalisis.orden_id == orden_id)
            .order_by(HistorialOrdenAnalisis.changed_at.asc())
        )
        return list(self.db.scalars(query).all())
