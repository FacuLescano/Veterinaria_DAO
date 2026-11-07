from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.orden_analisis import DetalleOrdenAnalisis, OrdenAnalisis


class OrdenAnalisisDAO:

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, orden_id: int) -> OrdenAnalisis | None:
        query = (
            select(OrdenAnalisis)
            .where(OrdenAnalisis.id == orden_id)
            .options(
                selectinload(OrdenAnalisis.detalles).selectinload(DetalleOrdenAnalisis.tipo_analisis),
                selectinload(OrdenAnalisis.consulta),
                selectinload(OrdenAnalisis.veterinario),
            )
        )
        return self.db.scalars(query).first()

    def list_by_consulta_id(self, consulta_id: int) -> list[OrdenAnalisis]:
        query = (
            select(OrdenAnalisis)
            .where(OrdenAnalisis.consulta_id == consulta_id)
            .options(
                selectinload(OrdenAnalisis.detalles).selectinload(DetalleOrdenAnalisis.tipo_analisis),
                selectinload(OrdenAnalisis.consulta),
                selectinload(OrdenAnalisis.veterinario),
            )
            .order_by(OrdenAnalisis.created_at.desc())
        )
        return list(self.db.scalars(query).all())

    def list_all(self) -> list[OrdenAnalisis]:
        query = (
            select(OrdenAnalisis)
            .options(
                selectinload(OrdenAnalisis.detalles).selectinload(DetalleOrdenAnalisis.tipo_analisis),
                selectinload(OrdenAnalisis.consulta),
                selectinload(OrdenAnalisis.veterinario),
            )
            .order_by(OrdenAnalisis.created_at.desc())
        )
        return list(self.db.scalars(query).all())

    def create(self, orden: OrdenAnalisis) -> OrdenAnalisis:
        self.db.add(orden)
        self.db.flush()
        return orden
