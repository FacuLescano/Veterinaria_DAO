from datetime import datetime
from uuid import uuid4
from pydantic import BaseModel, ConfigDict, Field


# --- Schemas para Tipos de Muestra ---

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


# --- Schemas para TipoAnalisis ---

class TipoAnalisisBase(BaseModel):
    nombre: str = Field(..., max_length=120, description="Nombre del tipo de análisis (ej: Hemograma)")
    descripcion: str | None = Field(default=None, description="Descripción opcional del análisis")


class TipoAnalisisCreate(TipoAnalisisBase):
    tipos_muestra_compatibles_ids: list[int] = Field(
        default=[], description="IDs de tipos de muestra biológica compatibles con este análisis"
    )


class ConfigurarCompatibilidadCreate(BaseModel):
    tipos_muestra_ids: list[int] = Field(
        ..., description="Lista de IDs de tipos de muestra biológica compatibles con este tipo de análisis"
    )


class TipoAnalisisRead(TipoAnalisisBase):
    id: int
    activo: bool
    tipos_muestra_compatibles: list[TipoMuestraRead] = []

    model_config = ConfigDict(from_attributes=True)


# --- Schemas para Asociación Detalle - Muestra (US-09) ---

class AsociacionDetalleMuestraRead(BaseModel):
    id: int
    detalle_id: int
    muestra_id: int
    fecha_asociacion: datetime
    observaciones: str | None = None

    model_config = ConfigDict(from_attributes=True)


class AsociarMuestraAnalisisCreate(BaseModel):
    muestra_id: int = Field(..., description="ID de la muestra biológica a vincular")
    detalle_ids: list[int] = Field(
        ..., min_length=1, description="Lista de IDs de análisis solicitados (detalles) a satisfacer con esta muestra"
    )
    observaciones: str | None = Field(
        default=None, max_length=300, description="Observaciones opcionales sobre la asociación o idoneidad"
    )


class ResultadoAsociacionRead(BaseModel):
    muestra_id: int
    detalles_asociados: list[int]
    mensaje: str


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
    tiene_muestra: bool = False
    asociaciones_muestras: list[AsociacionDetalleMuestraRead] = []

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


# --- Schemas para OrdenAnalisis ---

class SolicitudAnalisisCreate(BaseModel):
    consulta_id: int = Field(..., description="ID de la consulta médica que origina la solicitud")
    veterinario_id: int | None = Field(default=None, description="ID del veterinario solicitante (opcional, por defecto toma el de la consulta)")
    observaciones: str | None = Field(default=None, description="Observaciones generales sobre la solicitud")
    detalles: list[DetalleOrdenAnalisisCreate] = Field(..., min_length=1, description="Lista de análisis solicitados con sus indicaciones")


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
        default_factory=lambda: f"TUB-{uuid4().hex.upper()}",
        min_length=1,
        max_length=60,
        description="Rótulo único del contenedor. Se genera automáticamente cuando se omite.",
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
    muestras: list[MuestraRead] = []

    model_config = ConfigDict(from_attributes=True)


# --- Schemas para Estado de Orden y Muestras ---

class MuestraEstadoUpdate(BaseModel):
    nuevo_estado: str = Field(
        ...,
        description="Estado operativo de la muestra: extraida, pendiente_preparacion, lista_para_envio o con_inconveniente. El empaquetado y despacho se registran mediante el envío.",
    )
    responsable: str = Field(
        ..., min_length=1, max_length=160, description="Nombre o cargo de quien realiza el cambio de estado"
    )
    motivo: str | None = Field(
        default=None, max_length=500, description="Motivo del cambio de estado o detalle del inconveniente"
    )


class ResumenEstadoMuestrasRead(BaseModel):
    total: int
    registradas: int
    pendientes_preparacion: int
    listas_para_envio: int
    empaquetadas: int = 0
    enviadas: int
    con_inconvenientes: int


class SeguimientoOrdenMuestrasRead(BaseModel):
    orden_id: int
    estado_orden: str
    paciente_nombre: str | None = None
    resumen_muestras: ResumenEstadoMuestrasRead
    muestras_listas_para_enviar: list[MuestraRead] = []
    muestras_pendientes_preparacion: list[MuestraRead] = []
    muestras_con_inconvenientes: list[MuestraRead] = []
    analisis_sin_muestra: list[DetalleOrdenAnalisisRead] = []
    lista_para_despacho: bool

