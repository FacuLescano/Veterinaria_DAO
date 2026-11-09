from fastapi import FastAPI

from app.api.patients import router as enrutador_pacientes
from app.db.session import ModeloBase, engine
from app.models import patient  # Registra las entidades en el metadata de SQLAlchemy.

app = FastAPI(
    title="Sistema de Gestión Veterinaria",
    description="API de gestión de pacientes y atención veterinaria.",
    version="0.2.0",
)

app.include_router(enrutador_pacientes)


@app.on_event("startup")
def crear_tablas_de_base_de_datos():
    ModeloBase.metadata.create_all(bind=engine)


@app.get("/")
def inicio():
    return {
        "mensaje": "Sistema de Gestión Veterinaria",
        "documentacion": "/docs",
        "estado": "en funcionamiento",
    }


@app.get("/health", tags=["Sistema"])
def verificar_estado():
    return {"status": "ok", "message": "La API está funcionando"}
