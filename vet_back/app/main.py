
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import inspect, text

from app.api.ordenes_analisis import router as ordenes_analisis_router
from app.api.envios import router as envios_router
from app.api.patients import router as patients_router
from app.api.recepcion import enrutador as recepcion_router
from app.db.session import Base, engine
from app.db.recepcion import inicializar_base as inicializar_base_recepcion
from app.models import envio  # Registra las entidades de despacho en el metadata.
from app.models import orden_analisis, patient  # Registra las entidades en el metadata de SQLAlchemy.

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    envio_columns = {column["name"] for column in inspect(engine).get_columns("envios")}
    if "condiciones_empaquetado" not in envio_columns:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "ALTER TABLE envios ADD COLUMN condiciones_empaquetado "
                    "VARCHAR(500) NOT NULL DEFAULT 'Sin especificar (registro previo)'"
                )
            )
    inicializar_base_recepcion()
    yield

app = FastAPI(
    title="Sistema de Gestión Veterinaria",
    description="API de gestión veterinaria: pacientes, atención clínica y órdenes de análisis.",
    version="0.3.0",
)

app.include_router(enrutador_pacientes)
app.include_router(ordenes_analisis_router)
app.include_router(envios_router)
app.include_router(recepcion_router, prefix="/api/v1")

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
