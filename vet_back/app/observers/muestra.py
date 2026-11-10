from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from sqlalchemy.orm import Session


@dataclass(frozen=True)
class CambioEstadoMuestra:
    muestra_id: int
    codigo_etiqueta: str
    orden_id: int
    veterinario_id: int
    estado_anterior: str | None
    estado_nuevo: str
    ocurrido_en: datetime
    motivo: str | None


class ObservadorEstadoMuestra(Protocol):
    def actualizar(self, evento: CambioEstadoMuestra, sesion: Session) -> None: ...


class SujetoEstadoMuestra:
    def __init__(self) -> None:
        self._observadores: list[ObservadorEstadoMuestra] = []

    def suscribir(self, observador: ObservadorEstadoMuestra) -> None:
        if not any(actual is observador for actual in self._observadores):
            self._observadores.append(observador)

    def desuscribir(self, observador: ObservadorEstadoMuestra) -> None:
        self._observadores = [actual for actual in self._observadores if actual is not observador]

    def notificar(self, evento: CambioEstadoMuestra, sesion: Session) -> None:
        for observador in tuple(self._observadores):
            observador.actualizar(evento, sesion)


class NotificarVeterinario:
    """Guarda una notificación en la bandeja del veterinario responsable."""

    def actualizar(self, evento: CambioEstadoMuestra, sesion: Session) -> None:
        from app.models.notificacion import NotificacionVeterinario

        estado_anterior = evento.estado_anterior or "sin estado previo"
        sesion.add(
            NotificacionVeterinario(
                veterinario_id=evento.veterinario_id,
                muestra_id=evento.muestra_id,
                estado_anterior=evento.estado_anterior,
                estado_nuevo=evento.estado_nuevo,
                mensaje=(
                    f"La muestra {evento.codigo_etiqueta} cambió de "
                    f"{estado_anterior} a {evento.estado_nuevo}."
                ),
                motivo=evento.motivo,
                ocurrido_en=evento.ocurrido_en,
            )
        )


estado_muestra = SujetoEstadoMuestra()


def publicar_cambio_estado(evento: CambioEstadoMuestra, sesion: Session) -> None:
    estado_muestra.notificar(evento, sesion)
