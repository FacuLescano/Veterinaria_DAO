from fastapi import FastAPI

from app.api.ordenes_analisis import router as ordenes_analisis_router
from app.api.patients import router as enrutador_pacientes
try:
    from app.db.session import ModeloBase, engine
except ImportError:
    from app.db.session import Base as ModeloBase, engine
from app.models import orden_analisis, patient  # Registra las entidades en el metadata de SQLAlchemy.

app = FastAPI(
    title="Sistema de Gestión Veterinaria",
    description="API de gestión veterinaria: pacientes, atención clínica y órdenes de análisis.",
    version="0.3.0",
)

app.include_router(enrutador_pacientes)
app.include_router(ordenes_analisis_router)


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
