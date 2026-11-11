"""Adaptador de lectura de despachos para el módulo 4."""
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
    from app.db.session import SessionLocal
    from app.models.envio import Envio

    with SessionLocal() as sesion:
        envios = sesion.query(Envio).filter(Envio.estado == "despachado").all()
        return [
            EnvioDespachado(
                envio_id=str(envio.id),
                fecha_despacho=envio.fecha_despacho,
                remito_id=envio.remito.numero if envio.remito else str(envio.id),
                muestras_ids=[str(muestra.id) for muestra in envio.muestras],
                conservadoras_ids=[str(conservadora.id) for conservadora in envio.conservadoras],
                precintos=[
                    {"id": str(precinto.id), "codigo": precinto.codigo, "conservadora_id": str(precinto.conservadora_id)}
                    for precinto in envio.precintos
                ],
            )
            for envio in envios
        ]
