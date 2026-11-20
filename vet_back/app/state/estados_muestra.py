from abc import ABC, abstractmethod
from typing import ClassVar


class TransicionMuestraInvalida(ValueError):
    """Se intenta ejecutar una operación que el estado actual no permite."""


class EstadoMuestra(ABC):
    """Contrato State. Los objetos de estado no realizan persistencia."""

    codigo: ClassVar[str]
    codigo_persistido: ClassVar[str]

    @property
    @abstractmethod
    def nombre(self) -> str:
        """Nombre estable del estado para mensajes y diagnóstico."""

    def iniciar_preparacion(self, muestra: object, motivo: str | None = None) -> "EstadoMuestra":
        self._rechazar("iniciar preparación")

    def marcar_lista_para_envio(self, muestra: object, motivo: str | None = None) -> "EstadoMuestra":
        self._rechazar("marcar lista para envío")

    def empaquetar(self, muestra: object) -> "EstadoMuestra":
        self._rechazar("empaquetar")

    def despachar(self, muestra: object) -> "EstadoMuestra":
        self._rechazar("despachar")

    def recibir(self, muestra: object) -> "EstadoMuestra":
        self._rechazar("registrar recepción")

    def registrar_analisis(self, muestra: object, referencia_resultado: str) -> "EstadoMuestra":
        self._rechazar("registrar análisis")

    def rechazar(self, muestra: object, motivo: str) -> "EstadoMuestra":
        self._rechazar("rechazar")

    def reportar_inconveniente(self, muestra: object, motivo: str | None = None) -> "EstadoMuestra":
        self._rechazar("reportar inconveniente")

    def _rechazar(self, operacion: str) -> None:
        raise TransicionMuestraInvalida(
            f"No se puede {operacion} una muestra en estado '{self.codigo}'"
        )


class EstadoExtraida(EstadoMuestra):
    codigo = "extraida"
    codigo_persistido = "extraida"

    @property
    def nombre(self) -> str:
        return "Extraída"

    def iniciar_preparacion(self, muestra: object, motivo: str | None = None) -> EstadoMuestra:
        return EstadoPendientePreparacion()

    # Se conserva esta transición directa para no romper clientes existentes que
    # ya marcan una muestra como lista después de prepararla fuera del sistema.
    def marcar_lista_para_envio(self, muestra: object, motivo: str | None = None) -> EstadoMuestra:
        return EstadoListaParaEnvio()

    def reportar_inconveniente(self, muestra: object, motivo: str | None = None) -> EstadoMuestra:
        return EstadoConInconveniente()


class EstadoPendientePreparacion(EstadoMuestra):
    codigo = "pendiente_preparacion"
    codigo_persistido = "pendiente_preparacion"

    @property
    def nombre(self) -> str:
        return "Pendiente de preparación"

    def marcar_lista_para_envio(self, muestra: object, motivo: str | None = None) -> EstadoMuestra:
        return EstadoListaParaEnvio()

    def reportar_inconveniente(self, muestra: object, motivo: str | None = None) -> EstadoMuestra:
        return EstadoConInconveniente()


class EstadoListaParaEnvio(EstadoMuestra):
    codigo = "lista_para_envio"
    codigo_persistido = "lista_para_envio"

    @property
    def nombre(self) -> str:
        return "Lista para envío"

    def empaquetar(self, muestra: object) -> EstadoMuestra:
        return EstadoEmpaquetada()

    def reportar_inconveniente(self, muestra: object, motivo: str | None = None) -> EstadoMuestra:
        return EstadoConInconveniente()


class EstadoEmpaquetada(EstadoMuestra):
    codigo = "empaquetada"
    codigo_persistido = "empaquetada"

    @property
    def nombre(self) -> str:
        return "Empaquetada"

    def despachar(self, muestra: object) -> EstadoMuestra:
        return EstadoEnTransito()

    def reportar_inconveniente(self, muestra: object, motivo: str | None = None) -> EstadoMuestra:
        return EstadoConInconveniente()


class EstadoEnTransito(EstadoMuestra):
    codigo = "en_transito"
    # `enviada` es el código histórico de la API y de la base existente.
    codigo_persistido = "enviada"

    @property
    def nombre(self) -> str:
        return "En tránsito"

    def recibir(self, muestra: object) -> EstadoMuestra:
        return EstadoRecibida()

    def reportar_inconveniente(self, muestra: object, motivo: str | None = None) -> EstadoMuestra:
        return EstadoConInconveniente()


class EstadoRecibida(EstadoMuestra):
    codigo = "recibida"
    codigo_persistido = "recibida"

    @property
    def nombre(self) -> str:
        return "Recibida"

    def registrar_analisis(self, muestra: object, referencia_resultado: str) -> EstadoMuestra:
        if not referencia_resultado or not referencia_resultado.strip():
            raise ValueError("Se requiere una referencia al resultado recibido")
        return EstadoAnalizada()

    def rechazar(self, muestra: object, motivo: str) -> EstadoMuestra:
        if not motivo.strip():
            raise ValueError("El rechazo debe incluir un motivo")
        return EstadoRechazada()

    def reportar_inconveniente(self, muestra: object, motivo: str | None = None) -> EstadoMuestra:
        return EstadoConInconveniente()


class EstadoAnalizada(EstadoMuestra):
    codigo = "analizada"
    codigo_persistido = "analizada"

    @property
    def nombre(self) -> str:
        return "Analizada"


class EstadoRechazada(EstadoMuestra):
    codigo = "rechazada"
    codigo_persistido = "rechazada"

    @property
    def nombre(self) -> str:
        return "Rechazada"


class EstadoConInconveniente(EstadoMuestra):
    codigo = "con_inconveniente"
    codigo_persistido = "con_inconveniente"

    @property
    def nombre(self) -> str:
        return "Con inconveniente"

    def marcar_lista_para_envio(self, muestra: object, motivo: str | None = None) -> EstadoMuestra:
        if not motivo or not motivo.strip():
            raise ValueError("La resolución del inconveniente debe incluir un motivo")
        return EstadoListaParaEnvio()


_ESTADOS: dict[str, type[EstadoMuestra]] = {
    estado.codigo: estado
    for estado in (
        EstadoExtraida,
        EstadoPendientePreparacion,
        EstadoListaParaEnvio,
        EstadoEmpaquetada,
        EstadoEnTransito,
        EstadoRecibida,
        EstadoAnalizada,
        EstadoRechazada,
        EstadoConInconveniente,
    )
}
_ESTADOS[EstadoEnTransito.codigo_persistido] = EstadoEnTransito


def crear_estado_muestra(codigo: str) -> EstadoMuestra:
    """Reconstruye el objeto de estado a partir del código guardado en SQL."""
    estado = _ESTADOS.get(codigo.strip().lower())
    if estado is None:
        raise TransicionMuestraInvalida(f"Código de estado de muestra desconocido: '{codigo}'")
    return estado()
