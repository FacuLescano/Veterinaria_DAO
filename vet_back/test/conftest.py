from datetime import date
from pathlib import Path
import sys
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from app.db.session import ModeloBase, obtener_sesion_bd
except ImportError:
    from app.db.session import Base as ModeloBase, get_db as obtener_sesion_bd

from app.main import app
from app.models.orden_analisis import TipoAnalisis, TipoMuestra

try:
    from app.models.paciente import Consulta, Mascota, Responsable, Veterinario
except ImportError:
    from app.models.paciente import (
        Consultation as Consulta,
        Pet as Mascota,
        Responsible as Responsable,
        Veterinarian as Veterinario,
    )

# Base de datos en memoria para no modificar veterinaria.db
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def setup_database():
    """Crea las tablas antes de cada test y las limpia al terminar."""
    ModeloBase.metadata.create_all(bind=engine)
    yield
    ModeloBase.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    """Cliente HTTP para hacer peticiones a la API en los tests."""
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[obtener_sesion_bd] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def datos_prueba():
    """Crea datos mínimos de prueba: 1 responsable, 1 veterinario, 1 mascota, 1 consulta y 1 tipo de análisis."""
    db = TestingSessionLocal()
    try:
        resp = Responsable(
            document_number="12345678",
            full_name="Juan Perez",
            phone="1122334455",
        )
        db.add(resp)
        db.flush()

        vet = Veterinario(
            full_name="Dra. Lopez",
            license_number="MP-9988",
            active=True,
        )
        db.add(vet)
        db.flush()

        pet = Mascota(
            responsible_id=resp.id,
            name="Firulais",
            species="Canino",
        )
        db.add(pet)
        db.flush()

        consulta = Consulta(
            pet_id=pet.id,
            veterinarian_id=vet.id,
            reason="Control general",
        )
        db.add(consulta)
        db.flush()

        tipo = TipoAnalisis(
            nombre="Hemograma Completo",
            descripcion="Recuento sanguíneo",
            activo=True,
        )
        db.add(tipo)

        tipo_muestra = TipoMuestra(
            nombre="Sangre con EDTA",
            descripcion="Tubo con anticoagulante EDTA",
            condiciones_conservacion_default="Refrigerar a 4°C",
            activo=True,
        )
        db.add(tipo_muestra)
        db.commit()

        return {
            "consulta_id": consulta.id,
            "veterinario_id": vet.id,
            "tipo_analisis_id": tipo.id,
            "tipo_muestra_id": tipo_muestra.id,
        }
    finally:
        db.close()
