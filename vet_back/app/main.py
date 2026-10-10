
from fastapi import FastAPI

app = FastAPI(
    title="Sistema de Gestión Veterinaria",
    description="API para la red de clínicas veterinarias y el laboratorio central.",
    version="0.1.0",
)

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
