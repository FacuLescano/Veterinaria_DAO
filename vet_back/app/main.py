from fastapi import FastAPI

from app.api.patients import router as patients_router
from app.db.session import Base, engine
from app.models import patient  # Registra las entidades en el metadata de SQLAlchemy.

app = FastAPI(
    title="Sistema de Gestión Veterinaria",
    description="API de gestión de pacientes y atención veterinaria.",
    version="0.2.0",
)

app.include_router(patients_router)


@app.on_event("startup")
def create_database_tables():
    Base.metadata.create_all(bind=engine)


@app.get("/")
def inicio():
    return {
        "mensaje": "Sistema de Gestión Veterinaria",
        "documentacion": "/docs",
        "estado": "en funcionamiento",
    }


@app.get("/health", tags=["Sistema"])
def health_check():
    return {"status": "ok", "message": "La API está funcionando"}
