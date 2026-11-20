from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.orden_analisis import MuestraRead


class ConservadoraCreate(BaseModel):
    codigo: str = Field(..., min_length=1, max_length=60)
    descripcion: str | None = Field(default=None, max_length=300)

    @field_validator("codigo")
    @classmethod
    def limpiar_codigo(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("El código no puede estar vacío")
        return value


class ConservadoraRead(BaseModel):
    id: int
    codigo: str
    descripcion: str | None
    disponible: bool

    model_config = ConfigDict(from_attributes=True)


class ContenidoConservadoraCreate(BaseModel):
    conservadora_id: int
    muestra_ids: list[int] = Field(..., min_length=1)


class EnvioCreate(BaseModel):
    origen: str = Field(..., min_length=1, max_length=160)
    destino: str = Field(..., min_length=1, max_length=160)
    condiciones_empaquetado: str = Field(..., min_length=1, max_length=500)
    responsable_preparacion: str = Field(default="Sistema", min_length=1, max_length=160)
    conservadoras: list[ContenidoConservadoraCreate] = Field(..., min_length=1)
    observaciones: str | None = None

    @field_validator("origen", "destino", "condiciones_empaquetado", "responsable_preparacion")
    @classmethod
    def limpiar_requerido(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("El campo no puede estar vacío")
        return value


class DespachoCreate(BaseModel):
    responsable_despacho: str = Field(..., min_length=1, max_length=160)
    transportista: str = Field(..., min_length=1, max_length=160)
    fecha_despacho: datetime | None = None
    observaciones: str | None = None

    @field_validator("responsable_despacho", "transportista")
    @classmethod
    def limpiar_responsable(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("El campo no puede estar vacío")
        return value


class PrecintoCreate(BaseModel):
    codigo: str = Field(..., min_length=1, max_length=80)
    conservadora_id: int
    colocado_por: str = Field(..., min_length=1, max_length=160)
    fecha_colocacion: datetime | None = None

    @field_validator("codigo", "colocado_por")
    @classmethod
    def limpiar_identificacion(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("El campo no puede estar vacío")
        return value


class VerificacionPrecintoCreate(BaseModel):
    conservadora_id: int
    codigo_observado: str | None = Field(default=None, max_length=80)
    resultado: str = Field(..., pattern="^(integro|roto|ausente|codigo_no_coincide)$")
    fecha_verificacion: datetime | None = None
    responsable: str = Field(..., min_length=1, max_length=160)
    observaciones: str | None = None

    @field_validator("codigo_observado", "responsable")
    @classmethod
    def limpiar_verificacion(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None


class PrecintoRead(BaseModel):
    id: int
    codigo: str
    envio_id: int
    conservadora_id: int
    colocado_por: str
    fecha_colocacion: datetime
    estado: str
    verificaciones: list["VerificacionPrecintoRead"] = []

    model_config = ConfigDict(from_attributes=True)


class VerificacionPrecintoRead(BaseModel):
    id: int
    envio_id: int
    conservadora_id: int
    precinto_id: int | None
    codigo_observado: str | None
    resultado: str
    fecha_verificacion: datetime
    responsable: str
    observaciones: str | None

    model_config = ConfigDict(from_attributes=True)


class RegistroTemperaturaCreate(BaseModel):
    conservadora_id: int
    muestra_id: int | None = None
    temperatura_requerida_c: float | None = None
    temperatura_medida_c: float = Field(allow_inf_nan=False, strict=True)
    unidad: str = Field(default="°C", min_length=1, max_length=12)
    fecha_medicion: datetime
    responsable: str = Field(..., min_length=1, max_length=160)
    dispositivo: str | None = Field(default=None, max_length=160)
    observaciones: str | None = None

    @field_validator("responsable")
    @classmethod
    def limpiar_medicion(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("El campo no puede estar vacío")
        return value

    @field_validator("unidad")
    @classmethod
    def validar_unidad_celsius(cls, value: str) -> str:
        if value.strip().upper().replace("º", "°") not in {"°C", "C"}:
            raise ValueError("La temperatura de salida se registra en grados Celsius.")
        return "°C"


class RegistroTemperaturaRead(BaseModel):
    id: int
    envio_id: int
    conservadora_id: int | None
    muestra_id: int | None
    temperatura_requerida_c: float | None
    temperatura_medida_c: float
    unidad: str
    fecha_medicion: datetime
    responsable: str
    dispositivo: str | None
    observaciones: str | None

    model_config = ConfigDict(from_attributes=True)


class IncidenciaTransporteCreate(BaseModel):
    conservadora_id: int | None = None
    muestra_id: int | None = None
    tipo: str = Field(..., min_length=1, max_length=80)
    descripcion: str = Field(..., min_length=1)
    fecha_evento: datetime
    responsable: str = Field(..., min_length=1, max_length=160)

    @field_validator("tipo", "descripcion", "responsable")
    @classmethod
    def limpiar_incidencia(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("El campo no puede estar vacío")
        return value


class IncidenciaTransporteRead(BaseModel):
    id: int
    envio_id: int
    conservadora_id: int | None
    muestra_id: int | None
    tipo: str
    descripcion: str
    fecha_evento: datetime
    responsable: str

    model_config = ConfigDict(from_attributes=True)


class ContenidoConservadoraRead(BaseModel):
    conservadora: ConservadoraRead
    muestra_ids: list[int]
    precintos: list[PrecintoRead]


class RemitoRead(BaseModel):
    id: int
    numero: str
    envio_id: int
    fecha_emision: datetime
    contenido: dict


class HistorialEnvioRead(BaseModel):
    id: int
    envio_id: int
    estado_anterior: str | None
    estado_nuevo: str
    fecha_evento: datetime
    responsable: str
    observaciones: str | None

    model_config = ConfigDict(from_attributes=True)


class EnvioRead(BaseModel):
    id: int
    origen: str
    destino: str
    transportista: str | None
    responsable_despacho: str | None
    estado: str
    fecha_creacion: datetime
    fecha_despacho: datetime | None
    condiciones_empaquetado: str
    observaciones: str | None
    muestras: list[MuestraRead]
    conservadoras: list[ContenidoConservadoraRead]
    precintos: list[PrecintoRead]
    remito: RemitoRead | None
    historial: list[HistorialEnvioRead]
    registros_temperatura: list[RegistroTemperaturaRead]
    incidencias: list[IncidenciaTransporteRead]


class EnvioResumenRead(BaseModel):
    id: int
    origen: str
    destino: str
    estado: str
    fecha_creacion: datetime
    fecha_despacho: datetime | None
    cantidad_muestras: int
    remito_numero: str | None
