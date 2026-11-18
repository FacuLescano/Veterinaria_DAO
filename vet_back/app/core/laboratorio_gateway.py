"""Contrato y adaptador determinista para consultar resultados externos."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Protocol


@dataclass(frozen=True)
class ResultadoExterno:
    detalle_id: str
    valores: list[dict]
    conclusion: str


@dataclass(frozen=True)
class RespuestaLaboratorio:
    muestra_id: str
    estado: str
    resultados: list[ResultadoExterno]
    mensaje: str = ""
    fecha_recepcion: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class LaboratorioGateway(Protocol):
    def consultar_resultados(self, muestra_id: str, analisis: list[dict], escenario: str) -> RespuestaLaboratorio: ...


class LaboratorioMock:
    """Simula respuestas de laboratorio sin gestionar procesos internos del laboratorio."""

    escenarios = {"completo", "multiples", "pendientes", "sin_resultados", "invalido"}

    def consultar_resultados(self, muestra_id: str, analisis: list[dict], escenario: str = "multiples") -> RespuestaLaboratorio:
        if escenario not in self.escenarios:
            raise ValueError(f"Escenario desconocido: {escenario}")
        if escenario == "pendientes":
            return RespuestaLaboratorio(muestra_id, "pendiente", [], "Los resultados aún no están disponibles.")
        if escenario == "sin_resultados":
            return RespuestaLaboratorio(muestra_id, "sin_resultados", [], "El laboratorio no informa resultados para este identificador.")
        resultados = [self._resultado(item, index, escenario) for index, item in enumerate(analisis)]
        if escenario == "invalido":
            resultados = [ResultadoExterno("detalle-ajeno", [], "")]
        return RespuestaLaboratorio(muestra_id, "disponible", resultados)

    @staticmethod
    def _resultado(analisis: dict, index: int, escenario: str) -> ResultadoExterno:
        nombre = str(analisis["nombre"]).lower()
        if "hemograma" in nombre:
            valores = [
                {"parametro": "Glóbulos rojos", "valor": "6.4", "unidad": "M/µL", "rangoReferencia": "5.5–8.5", "alerta": "Normal"},
                {"parametro": "Glóbulos blancos", "valor": "18.9", "unidad": "K/µL", "rangoReferencia": "6.0–17.0", "alerta": "Alto"},
            ]
        elif "renal" in nombre or "urea" in nombre or "creatinina" in nombre:
            valores = [
                {"parametro": "Urea", "valor": "42", "unidad": "mg/dL", "rangoReferencia": "20–60", "alerta": "Normal"},
                {"parametro": "Creatinina", "valor": "1.6", "unidad": "mg/dL", "rangoReferencia": "0.5–1.5", "alerta": "Alto"},
            ]
        elif "hepático" in nombre or "hepat" in nombre or "bioquím" in nombre:
            valores = [
                {"parametro": "ALT / GPT", "valor": "112", "unidad": "U/L", "rangoReferencia": "10–100", "alerta": "Alto"},
                {"parametro": "Fosfatasa alcalina", "valor": "75", "unidad": "U/L", "rangoReferencia": "20–150", "alerta": "Normal"},
            ]
        else:
            valores = [{"parametro": str(analisis["nombre"]), "valor": f"{index + 1}", "unidad": "resultado", "rangoReferencia": "Según método", "alerta": "Normal"}]
        if escenario == "completo":
            valores = [
                {**valor, "valor": {"Glóbulos blancos": "12.0", "Creatinina": "1.1", "ALT / GPT": "64"}.get(valor["parametro"], valor["valor"]), "alerta": "Normal"}
                for valor in valores
            ]
        return ResultadoExterno(str(analisis["detalle_id"]), valores, f"Resultado simulado para {analisis['nombre']}.")
