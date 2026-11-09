from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.orden_analisis import TipoAnalisis


class TipoAnalisisDAO:

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, tipo_id: int) -> TipoAnalisis | None:
        return self.db.get(TipoAnalisis, tipo_id)

    def get_by_nombre(self, nombre: str) -> TipoAnalisis | None:
        return self.db.scalars(
            select(TipoAnalisis).where(TipoAnalisis.nombre.ilike(nombre.strip()))
        ).first()

    def list_all(self, only_active: bool = True) -> list[TipoAnalisis]:
        query = select(TipoAnalisis).order_by(TipoAnalisis.nombre)
        if only_active:
            query = query.where(TipoAnalisis.activo == True)
        return list(self.db.scalars(query).all())

    def create(self, tipo: TipoAnalisis) -> TipoAnalisis:
        self.db.add(tipo)
        self.db.flush()
        return tipo
