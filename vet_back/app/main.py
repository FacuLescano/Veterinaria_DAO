
from fastapi import FastAPI
from app.api.modulo4 import enrutador as enrutador_modulo4
from app.db.modulo4 import inicializar_base

app = FastAPI(
    title="Sistema de Gestión Veterinaria",
    description="API para la red de clínicas veterinarias y el laboratorio central.",
    version="0.1.0",
)

app.include_router(enrutador_modulo4, prefix="/api/modulo4")


@app.on_event("startup")
def iniciar_persistencia_modulo4():
    inicializar_base()

@app.get("/")
def inicio():
    return {
        "mensaje": "Sistema de Gestión Veterinaria",
        "documentacion": "/docs",
        "estado": "en funcionamiento"
    }

@app.get("/health", tags=["Sistema"])
def health_check():
    return {
        "status": "ok",
        "message": "La API está funcionando",
    }
