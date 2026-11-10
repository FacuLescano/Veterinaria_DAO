from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.envio import (
    Conservadora,
    Envio,
    IncidenciaTransporte,
    PrecintoSanitario,
    RegistroTemperatura,
    Remito,
)
from app.models.orden_analisis import Muestra


class ConservadoraDAO:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, conservadora_id: int) -> Conservadora | None:
        return self.db.get(Conservadora, conservadora_id)

    def get_by_codigo(self, codigo: str) -> Conservadora | None:
        return self.db.scalars(
            select(Conservadora).where(Conservadora.codigo == codigo)
        ).first()

    def list_all(self) -> list[Conservadora]:
        return list(self.db.scalars(select(Conservadora).order_by(Conservadora.codigo)).all())

    def create(self, conservadora: Conservadora) -> Conservadora:
        self.db.add(conservadora)
        self.db.flush()
        return conservadora


class EnvioDAO:
    def __init__(self, db: Session):
        self.db = db

    def _query(self):
        return select(Envio).options(
            selectinload(Envio.muestras).selectinload(Muestra.tipo_muestra),
            selectinload(Envio.muestras).selectinload(Muestra.historial),
            selectinload(Envio.conservadoras),
            selectinload(Envio.precintos),
            selectinload(Envio.precintos).selectinload(PrecintoSanitario.verificaciones),
            selectinload(Envio.remito),
            selectinload(Envio.historial),
            selectinload(Envio.verificaciones_precinto),
            selectinload(Envio.registros_temperatura),
            selectinload(Envio.incidencias),
        )

    def get_by_id(self, envio_id: int) -> Envio | None:
        return self.db.scalars(self._query().where(Envio.id == envio_id)).first()

    def list_all(self) -> list[Envio]:
        query = self._query().order_by(Envio.fecha_creacion.desc())
        return list(self.db.scalars(query).all())

    def create(self, envio: Envio) -> Envio:
        self.db.add(envio)
        self.db.flush()
        return envio

    def get_precinto(self, envio_id: int, conservadora_id: int) -> PrecintoSanitario | None:
        return self.db.scalars(
            select(PrecintoSanitario).where(
                PrecintoSanitario.envio_id == envio_id,
                PrecintoSanitario.conservadora_id == conservadora_id,
            )
        ).first()

    def get_precinto_by_code(self, codigo: str) -> PrecintoSanitario | None:
        return self.db.scalars(
            select(PrecintoSanitario).where(PrecintoSanitario.codigo == codigo)
        ).first()

    def get_remito(self, envio_id: int) -> Remito | None:
        return self.db.scalars(select(Remito).where(Remito.envio_id == envio_id)).first()

    def get_temperature_by_id(self, registro_id: int) -> RegistroTemperatura | None:
        return self.db.get(RegistroTemperatura, registro_id)

    def get_incident_by_id(self, incidencia_id: int) -> IncidenciaTransporte | None:
        return self.db.get(IncidenciaTransporte, incidencia_id)
