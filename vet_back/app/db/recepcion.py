"""Las tablas del módulo 4 comparten la base de datos operativa principal."""

from sqlalchemy.orm import DeclarativeBase, sessionmaker
from app.db.session import engine


class BaseModulo4(DeclarativeBase):
    pass


motor = engine
FabricaSesionModulo4 = sessionmaker(bind=motor, autoflush=False, expire_on_commit=False)


def obtener_sesion():
    sesion = FabricaSesionModulo4()
    try:
        yield sesion
    finally:
        sesion.close()


def inicializar_base():
    from app.models import recepcion  # Registra las tablas antes de crear el esquema.

    BaseModulo4.metadata.create_all(bind=motor)
