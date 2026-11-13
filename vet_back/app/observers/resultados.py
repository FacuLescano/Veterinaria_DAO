from dataclasses import dataclass
import logging
from typing import Protocol

from sqlalchemy.orm import Session

from app.services.correo_service import ServicioCorreo

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ResultadosRegistrados:
    resultado_id: str
    paciente_id: str


@dataclass(frozen=True)
class ResultadoAnalisisRegistrado:
    """Evento único para una recepción que puede contener varios análisis."""
    resultado_ids: tuple[str, ...]
    paciente_id: str

    @property
    def resultado_id(self) -> str:
        return ",".join(self.resultado_ids)


class ObservadorResultados(Protocol):
    def actualizar_resultados(self, evento: ResultadosRegistrados | ResultadoAnalisisRegistrado, sesion: Session) -> None: ...


class SujetoResultados:
    def __init__(self) -> None:
        self._observadores: list[ObservadorResultados] = []

    def suscribir(self, observador: ObservadorResultados) -> None:
        if not any(actual is observador for actual in self._observadores):
            self._observadores.append(observador)

    def notificar(self, evento: ResultadosRegistrados | ResultadoAnalisisRegistrado, sesion: Session) -> None:
        for observador in tuple(self._observadores):
            observador.actualizar_resultados(evento, sesion)


class ResponsableMascotaObserver:
    def __init__(self, servicio_correo: ServicioCorreo | None = None) -> None:
        self.servicio_correo = servicio_correo or ServicioCorreo()

    def actualizar_resultados(self, evento: ResultadosRegistrados, sesion: Session) -> None:
        from app.models.paciente import Mascota, Responsable

        try:
            mascota = sesion.get(Mascota, int(evento.paciente_id))
            responsable = sesion.get(Responsable, mascota.responsible_id) if mascota else None
            if not responsable:
                logger.warning("No se pudo notificar: falta responsable para el paciente %s", evento.paciente_id)
                return
            if not responsable.email or not responsable.email.strip():
                logger.warning(
                    "No se envió el aviso de resultados %s: el responsable %s no tiene correo registrado",
                    evento.resultado_id,
                    responsable.id,
                )
                return
            self.servicio_correo.enviar_resultados_disponibles(
                responsable.email, responsable.full_name, mascota.name if mascota else None
            )
        except Exception:
            # El registro del resultado ya fue confirmado; una incidencia de aviso no lo invalida.
            logger.exception("Falló la preparación del aviso de resultados %s", evento.resultado_id)


resultados_analisis = SujetoResultados()
resultados_analisis.suscribir(ResponsableMascotaObserver())
