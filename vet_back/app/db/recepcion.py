"""Persistencia aislada del módulo 4, configurable por variables de entorno."""
import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


class BaseModulo4(DeclarativeBase):
    pass


def _crear_motor():
    url = os.getenv("MODULO4_DATABASE_URL")
    if not url:
        ruta = Path(os.getenv("MODULO4_DATABASE_PATH", "data/modulo4.db"))
        ruta.parent.mkdir(parents=True, exist_ok=True)
        url = f"sqlite:///{ruta.as_posix()}"
    return create_engine(url, connect_args={"check_same_thread": False} if url.startswith("sqlite") else {})


motor = _crear_motor()
FabricaSesionModulo4 = sessionmaker(bind=motor, autoflush=False, expire_on_commit=False)


def obtener_sesion():
    sesion = FabricaSesionModulo4()
    try:
        yield sesion
    finally:
        sesion.close()


def inicializar_base():
    from vet_back.app.models import recepcion  # Registra las tablas antes de crear el esquema.

    BaseModulo4.metadata.create_all(bind=motor)
