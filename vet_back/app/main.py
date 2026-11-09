from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.api.ordenes_analisis import router as ordenes_analisis_router
from app.api.patients import router as patients_router
from app.db.session import Base, engine
from app.models import orden_analisis, patient  # Registra las entidades en el metadata de SQLAlchemy.


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Sistema de Gestión Veterinaria",
    description="API de gestión veterinaria: pacientes, atención clínica y órdenes de análisis.",
    version="0.3.0",
    lifespan=lifespan,
)

app.include_router(patients_router)
app.include_router(ordenes_analisis_router)


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
