
from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from sqlalchemy import inspect, text

from app.core import configuracion as _configuracion  # Carga .env antes de construir el motor.
from app.api.ordenes_analisis import router as ordenes_analisis_router
from app.api.envios import router as envios_router
from app.api.patients import router as patients_router
from app.api.recepcion import enrutador as recepcion_router
from app.api.reportes import router as reportes_router
from app.db.session import Base, engine
from app.db.recepcion import inicializar_base as inicializar_base_recepcion
from app.models import envio  # Registra las entidades de despacho en el metadata.
from app.models import orden_analisis  # Registra las entidades en el metadata de SQLAlchemy.
from app.models import notificacion  # Registra la bandeja de notificaciones del veterinario.
from app.models import paciente
from app.services.correo_service import ServicioCorreo

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    if not ServicioCorreo().configuracion.disponible:
        logger.warning("SMTP no está configurado; los avisos por correo de resultados no están disponibles")
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
    pet_columns = {column["name"] for column in inspect(engine).get_columns("mascotas")}
    with engine.begin() as connection:
        for name, sql_type in (("weight_kg", "FLOAT"), ("microchip", "VARCHAR(100)"), ("photo_url", "TEXT")):
            if name not in pet_columns:
                connection.execute(text(f"ALTER TABLE mascotas ADD COLUMN {name} {sql_type}"))
    inicializar_base_recepcion()
    yield

app = FastAPI(
    title="Sistema de Gestión Veterinaria",
    description="API de gestión veterinaria: pacientes, atención clínica y órdenes de análisis.",
    version="0.3.0",
    lifespan=lifespan,
)

app.include_router(patients_router)
app.include_router(ordenes_analisis_router)
app.include_router(envios_router)
app.include_router(recepcion_router, prefix="/api/v1")
app.include_router(reportes_router)

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
