from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class EsquemaBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class RecepcionEntrada(EsquemaBase):
    envio_id: str = Field(min_length=1, max_length=100)
    fecha_recepcion: datetime
    responsable_id: str = Field(min_length=1, max_length=100)
    muestras_despachadas: list[str] = Field(min_length=1)
    muestras_recibidas: list[str]
    observaciones: str | None = None

    @field_validator("fecha_recepcion")
    @classmethod
    def normalizar_fecha(cls, valor):
        return valor if valor.tzinfo else valor.replace(tzinfo=timezone.utc)

    @model_validator(mode="after")
    def muestras_unicas(self):
        if len(set(self.muestras_despachadas)) != len(self.muestras_despachadas):
            raise ValueError("La lista despachada no puede repetir muestras")
        if len(set(self.muestras_recibidas)) != len(self.muestras_recibidas):
            raise ValueError("La lista recibida no puede repetir muestras")
        return self


class VerificacionPrecintoEntrada(EsquemaBase):
    envio_id: str = Field(min_length=1, max_length=100)
    precinto_id: str | None = None
    codigo_esperado: str | None = None
    codigo_observado: str | None = None
    estado: Literal["integro", "roto", "ausente", "otra_anomalia"]
    fecha_verificacion: datetime
    responsable_id: str = Field(min_length=1, max_length=100)
    observaciones: str | None = None

    @field_validator("fecha_verificacion")
    @classmethod
    def normalizar_fecha(cls, valor):
        return valor if valor.tzinfo else valor.replace(tzinfo=timezone.utc)


class IncidenciaEntrada(EsquemaBase):
    envio_id: str = Field(min_length=1, max_length=100)
    tipo: Literal["muestra_faltante", "muestra_sobrante", "muestra_no_coincidente", "precinto", "otra"]
    descripcion: str = Field(min_length=1)
    fecha: datetime
    responsable_id: str = Field(min_length=1, max_length=100)
    muestra_id: str | None = None
    conservadora_id: str | None = None
    precinto_id: str | None = None
    recepcion_id: str | None = None

    @field_validator("fecha")
    @classmethod
    def normalizar_fecha(cls, valor):
        return valor if valor.tzinfo else valor.replace(tzinfo=timezone.utc)


class ResolucionIncidenciaEntrada(EsquemaBase):
    resolucion: str = Field(min_length=1)
    responsable_resolucion_id: str = Field(min_length=1, max_length=100)
    resuelta_en: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("resuelta_en")
    @classmethod
    def normalizar_fecha(cls, valor):
        return valor if valor.tzinfo else valor.replace(tzinfo=timezone.utc)


class ResultadoEntrada(EsquemaBase):
    orden_id: str = Field(min_length=1, max_length=100)
    detalle_orden_id: str = Field(min_length=1, max_length=100)
    paciente_id: str = Field(min_length=1, max_length=100)
    muestra_id: str | None = None
    fecha_recepcion: datetime
    procedencia: str = Field(min_length=1, max_length=200)
    datos: dict = Field(default_factory=dict)
    informe_uri: str | None = None
    informe_nombre: str | None = Field(default=None, max_length=255)
    registrado_por: str = Field(min_length=1, max_length=100)

    @field_validator("fecha_recepcion")
    @classmethod
    def normalizar_fecha(cls, valor):
        return valor if valor.tzinfo else valor.replace(tzinfo=timezone.utc)


class CambioEstadoResultadoEntrada(EsquemaBase):
    estado: Literal["recibido", "en_revision", "validado"]


class InterpretacionEntrada(EsquemaBase):
    interpretacion_clinica: str = Field(min_length=1)
