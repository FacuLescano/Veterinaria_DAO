import pytest

from app.state.estados_muestra import TransicionMuestraInvalida
from app.models.orden_analisis import Muestra


def test_contexto_delega_transiciones_del_ciclo_de_vida():
    muestra = Muestra(estado="extraida")

    assert muestra.estado_actual.nombre == "Extraída"
    assert muestra.marcar_lista_para_envio() == ("extraida", "lista_para_envio")
    assert muestra.empaquetar() == ("lista_para_envio", "empaquetada")
    assert muestra.despachar() == ("empaquetada", "enviada")
    assert muestra.estado_actual.nombre == "En tránsito"
    assert muestra.recibir() == ("enviada", "recibida")
    assert muestra.registrar_analisis("INF-LAB-001") == ("recibida", "analizada")

    with pytest.raises(TransicionMuestraInvalida):
        muestra.rechazar("Resultado ya registrado")


def test_transicion_invalida_se_rechaza_en_el_estado_actual():
    muestra = Muestra(estado="extraida")

    with pytest.raises(TransicionMuestraInvalida, match="despachar"):
        muestra.despachar()


def test_rechazo_requiere_motivo_y_es_terminal():
    muestra = Muestra(estado="recibida")

    with pytest.raises(ValueError, match="motivo"):
        muestra.rechazar(" ")

    assert muestra.rechazar("Muestra insuficiente") == ("recibida", "rechazada")
    with pytest.raises(TransicionMuestraInvalida):
        muestra.recibir()
