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


# --- Schemas para Historial y Estado de Orden ---

class HistorialOrdenAnalisisRead(BaseModel):
    id: int
    orden_id: int
    estado_anterior: str | None
    estado_nuevo: str
    changed_at: datetime
    motivo: str | None = None

    model_config = ConfigDict(from_attributes=True)


class OrdenEstadoUpdate(BaseModel):
    nuevo_estado: str = Field(
        ...,
        description="Nuevo estado de la orden: solicitada, en_preparacion, enviada, con_resultados, cancelada",
    )
    motivo: str | None = Field(default=None, description="Motivo del cambio de estado o cancelación")


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
    paciente_id: int | None = None
    paciente_nombre: str | None = None
    veterinario_nombre: str | None = None
    detalles: list[DetalleOrdenAnalisisRead] = []

    model_config = ConfigDict(from_attributes=True)


# --- Schemas para Muestras Biológicas ---

class TipoMuestraBase(BaseModel):
    nombre: str = Field(..., max_length=120, description="Nombre del tipo de material biológico (ej: Sangre con EDTA, Orina)")
    descripcion: str | None = Field(default=None, description="Descripción del tipo de muestra")
    condiciones_conservacion_default: str | None = Field(
        default=None, max_length=200, description="Condiciones predeterminadas de conservación (ej: Refrigerar a 4°C)"
    )


class TipoMuestraCreate(TipoMuestraBase):
    pass


class TipoMuestraRead(TipoMuestraBase):
    id: int
    activo: bool

    model_config = ConfigDict(from_attributes=True)


class HistorialMuestraRead(BaseModel):
    id: int
    muestra_id: int
    estado_anterior: str | None
    estado_nuevo: str
    changed_at: datetime
    motivo: str | None = None
    responsable: str | None = None

    model_config = ConfigDict(from_attributes=True)


class MuestraCreate(BaseModel):
    codigo_etiqueta: str = Field(
        ...,
        min_length=1,
        max_length=60,
        description="Identificación física única o código de barra/etiqueta del contenedor",
    )
    orden_id: int = Field(..., description="ID de la orden de análisis a la que pertenece la muestra")
    tipo_muestra_id: int = Field(..., description="ID del tipo de material biológico")
    responsable_extraccion: str = Field(
        ..., min_length=1, max_length=160, description="Profesional o personal autorizado que realizó la extracción"
    )
    condiciones_conservacion: str | None = Field(
        default=None,
        max_length=200,
        description="Condiciones de conservación requeridas (si no se especifica, usa el valor por defecto del tipo de muestra)",
    )
    observaciones_calidad: str | None = Field(
        default=None, description="Observaciones iniciales sobre el estado o calidad de la muestra (ej: Hemolizada, Turbia)"
    )
    fecha_extraccion: datetime | None = Field(
        default=None, description="Fecha y hora de extracción (por defecto momento actual)"
    )


class MuestraRead(BaseModel):
    id: int
    codigo_etiqueta: str
    orden_id: int
    tipo_muestra_id: int
    fecha_extraccion: datetime
    responsable_extraccion: str
    condiciones_conservacion: str
    observaciones_calidad: str | None
    estado: str
    tipo_muestra: TipoMuestraRead | None = None
    historial: list[HistorialMuestraRead] = []

    model_config = ConfigDict(from_attributes=True)

