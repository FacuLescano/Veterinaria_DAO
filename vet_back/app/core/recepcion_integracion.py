"""Contratos de lectura para integrar los módulos 2 y 3 sin duplicar sus modelos.

Al integrar sus ramas, reemplazar ``listar_envios_despachados`` por un adaptador
que consulte el servicio/DAO dueño de Envio. El resto del módulo depende solo
de este contrato pequeño.
"""
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class EnvioDespachado:
    envio_id: str
    fecha_despacho: datetime
    remito_id: str
    muestras_ids: list[str]
    conservadoras_ids: list[str]
    precintos: list[dict]


def listar_envios_despachados() -> list[EnvioDespachado]:
    """Adaptador temporal vacío; el módulo 3 aporta su implementación al integrar."""
    return []
