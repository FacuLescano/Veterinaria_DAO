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
        motivo_normalizado = (evento.motivo or "").strip().lower()
        if "precinto" in motivo_normalizado or motivo_normalizado.startswith("recepción registrada en el laboratorio"):
            # La recepción ya publica su aviso con estado y condición del precinto.
            return
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


@dataclass(frozen=True)
class RecepcionMuestra:
    muestra_id: int
    codigo_etiqueta: str
    orden_id: int
    veterinario_id: int
    mascota_nombre: str | None
    resultado: str
    condicion_precinto: str
    ocurrido_en: datetime
    mensaje: str


class ObservadorRecepcion(Protocol):
    def actualizar_recepcion(self, evento: RecepcionMuestra, sesion: Session) -> None: ...


class SujetoRecepcionMuestra:
    def __init__(self) -> None:
        self._observadores: list[ObservadorRecepcion] = []

    def suscribir(self, observador: ObservadorRecepcion) -> None:
        if not any(actual is observador for actual in self._observadores):
            self._observadores.append(observador)

    def notificar(self, evento: RecepcionMuestra, sesion: Session) -> None:
        for observador in tuple(self._observadores):
            observador.actualizar_recepcion(evento, sesion)


class VeterinarioObserver:
    """Persiste en la bandeja compartida la recepción de cada muestra."""

    def actualizar_recepcion(self, evento: RecepcionMuestra, sesion: Session) -> None:
        from app.models.notificacion import NotificacionVeterinario

        sesion.add(NotificacionVeterinario(
            veterinario_id=evento.veterinario_id,
            muestra_id=evento.muestra_id,
            estado_anterior=None,
            estado_nuevo=evento.resultado,
            mensaje=evento.mensaje,
            motivo=f"Precinto: {evento.condicion_precinto}",
            ocurrido_en=evento.ocurrido_en,
        ))


recepcion_muestra = SujetoRecepcionMuestra()
recepcion_muestra.suscribir(VeterinarioObserver())


def publicar_recepcion_muestra(evento: RecepcionMuestra, sesion: Session) -> None:
    recepcion_muestra.notificar(evento, sesion)


estado_muestra = SujetoEstadoMuestra()


def publicar_cambio_estado(evento: CambioEstadoMuestra, sesion: Session) -> None:
    estado_muestra.notificar(evento, sesion)
