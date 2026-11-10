import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


class Base(DeclarativeBase):
    pass


def _obtener_url_base_datos() -> str:
    url = os.getenv("DATABASE_URL")
    if url:
        return url

    database_path = Path(os.getenv("DATABASE_PATH", "./data/veterinaria.db"))
    database_path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{database_path.as_posix()}"


DATABASE_URL = _obtener_url_base_datos()

engine = create_engine(
    DATABASE_URL,
    connect_args=(
        {"check_same_thread": False}
        if DATABASE_URL.startswith("sqlite")
        else {}
    ),
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)


def obtener_sesion_bd():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Compatibilidad con las rutas del módulo 2
get_db = obtener_sesion_bd