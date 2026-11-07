from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


# --- Schemas para TipoAnalisis ---

class TipoAnalisisBase(BaseModel):
    nombre: str = Field(..., max_length=120, description="Nombre del tipo de análisis (ej: Hemograma)")
    descripcion: str | None = Field(default=None, description="Descripción opcional del análisis")


class TipoAnalisisCreate(TipoAnalisisBase):
    pass


class TipoAnalisisRead(TipoAnalisisBase):
    id: int
    activo: bool

    model_config = ConfigDict(from_attributes=True)


# --- Schemas para DetalleOrdenAnalisis ---

class DetalleOrdenAnalisisCreate(BaseModel):
    tipo_analisis_id: int = Field(..., description="ID del tipo de análisis requerido")
    indicaciones: str | None = Field(default=None, description="Indicaciones clínicas o condiciones de preparación (ej: Ayuno 12 hs)")


class DetalleOrdenAnalisisRead(BaseModel):
    id: int
    orden_id: int
    tipo_analisis_id: int
    indicaciones: str | None
    estado: str
    tipo_analisis: TipoAnalisisRead | None = None

    model_config = ConfigDict(from_attributes=True)


# --- Schemas para US-06: Solicitar Análisis ---

class SolicitudAnalisisCreate(BaseModel):
    consulta_id: int = Field(..., description="ID de la consulta médica que origina la solicitud")
    veterinario_id: int | None = Field(default=None, description="ID del veterinario solicitante (opcional, por defecto toma el de la consulta)")
    observaciones: str | None = Field(default=None, description="Observaciones generales sobre la solicitud")
    detalles: list[DetalleOrdenAnalisisCreate] = Field(..., min_length=1, description="Lista de análisis solicitados con sus indicaciones")


class OrdenAnalisisRead(BaseModel):
    id: int
    consulta_id: int
    veterinario_id: int
    estado: str
    observaciones: str | None
    created_at: datetime
    detalles: list[DetalleOrdenAnalisisRead] = []

    model_config = ConfigDict(from_attributes=True)
