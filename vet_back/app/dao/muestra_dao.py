from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.orden_analisis import (
    AsociacionDetalleMuestra,
    HistorialMuestra,
    Muestra,
    TipoMuestra,
)


class TipoMuestraDAO:

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, tipo_id: int) -> TipoMuestra | None:
        return self.db.get(TipoMuestra, tipo_id)

    def get_by_nombre(self, nombre: str) -> TipoMuestra | None:
        return self.db.scalars(
            select(TipoMuestra).where(TipoMuestra.nombre.ilike(nombre.strip()))
        ).first()

    def list_all(self, only_active: bool = True) -> list[TipoMuestra]:
        query = select(TipoMuestra).order_by(TipoMuestra.nombre)
        if only_active:
            query = query.where(TipoMuestra.activo == True)
        return list(self.db.scalars(query).all())

    def create(self, tipo: TipoMuestra) -> TipoMuestra:
        self.db.add(tipo)
        self.db.flush()
        return tipo


class MuestraDAO:

    def __init__(self, db: Session):
        self.db = db

    def _default_options(self):
        return [
            selectinload(Muestra.tipo_muestra),
            selectinload(Muestra.historial),
            selectinload(Muestra.asociaciones_detalles),
        ]

    def get_by_id(self, muestra_id: int) -> Muestra | None:
        query = (
            select(Muestra)
            .where(Muestra.id == muestra_id)
            .options(*self._default_options())
        )
        return self.db.scalars(query).first()

    def get_by_codigo_etiqueta(self, codigo_etiqueta: str) -> Muestra | None:
        query = (
            select(Muestra)
            .where(Muestra.codigo_etiqueta == codigo_etiqueta.strip())
            .options(*self._default_options())
        )
        return self.db.scalars(query).first()

    def list_by_orden_id(self, orden_id: int) -> list[Muestra]:
        query = (
            select(Muestra)
            .where(Muestra.orden_id == orden_id)
            .options(*self._default_options())
            .order_by(Muestra.fecha_extraccion.desc())
        )
        return list(self.db.scalars(query).all())

    def create(self, muestra: Muestra) -> Muestra:
        self.db.add(muestra)
        self.db.flush()
        return muestra

    def add_historial(self, historial: HistorialMuestra) -> HistorialMuestra:
        self.db.add(historial)
        self.db.flush()
        return historial


class AsociacionMuestraDAO:

    def __init__(self, db: Session):
        self.db = db

    def get_by_detalle_and_muestra(
        self, detalle_id: int, muestra_id: int
    ) -> AsociacionDetalleMuestra | None:
        query = select(AsociacionDetalleMuestra).where(
            AsociacionDetalleMuestra.detalle_id == detalle_id,
            AsociacionDetalleMuestra.muestra_id == muestra_id,
        )
        return self.db.scalars(query).first()

    def list_by_detalle_id(self, detalle_id: int) -> list[AsociacionDetalleMuestra]:
        query = select(AsociacionDetalleMuestra).where(
            AsociacionDetalleMuestra.detalle_id == detalle_id
        )
        return list(self.db.scalars(query).all())

    def create(self, asociacion: AsociacionDetalleMuestra) -> AsociacionDetalleMuestra:
        self.db.add(asociacion)
        self.db.flush()
        return asociacion


