
from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from sqlalchemy import MetaData, inspect, text
from sqlalchemy.schema import CreateIndex, CreateTable

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
from app.models.paciente import Turno
from app.services.correo_service import ServicioCorreo

logger = logging.getLogger(__name__)


def _migrar_indice_horario_turno():
    """Quita la antigua restricción exacta, que también bloqueaba turnos cancelados."""
    if engine.dialect.name != "sqlite":
        return
    constraints = inspect(engine).get_unique_constraints("turnos")
    if not any(c.get("name") == "uq_vet_turno_horario" for c in constraints):
        return

    metadata_temporal = MetaData()
    for tabla in Base.metadata.tables.values():
        tabla.to_metadata(
            metadata_temporal,
            name="turnos_migracion" if tabla.name == "turnos" else None,
        )
    tabla_temporal = metadata_temporal.tables["turnos_migracion"]
    columnas = [column.name for column in Turno.__table__.columns]
    campos = ", ".join(f'"{nombre}"' for nombre in columnas)
    connection = engine.connect()
    try:
        connection.exec_driver_sql("PRAGMA foreign_keys=OFF")
        connection.commit()
        with connection.begin():
            connection.execute(CreateTable(tabla_temporal))
            connection.exec_driver_sql(
                f"INSERT INTO turnos_migracion ({campos}) SELECT {campos} FROM turnos"
            )
            connection.exec_driver_sql("DROP TABLE turnos")
            connection.exec_driver_sql("ALTER TABLE turnos_migracion RENAME TO turnos")
            for index in Turno.__table__.indexes:
                connection.execute(CreateIndex(index))
        connection.exec_driver_sql("PRAGMA foreign_keys=ON")
        connection.commit()
    finally:
        connection.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    if not ServicioCorreo().configuracion.disponible:
        logger.warning("SMTP no está configurado; los avisos por correo de resultados no están disponibles")
    Base.metadata.create_all(bind=engine)
    _migrar_indice_horario_turno()
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
