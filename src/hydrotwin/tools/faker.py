from __future__ import annotations

from datetime import datetime
import random
import threading

_estado_bancadas: dict[int, dict] = {}
_estado_lock = threading.Lock()


def inicializar_estado_bancada() -> dict:
    return {
        "ph": random.uniform(5.8, 6.2),
        "ec": random.uniform(1.0, 1.5),
        "temp_ar": random.uniform(20.0, 26.0),
        "temp_agua": random.uniform(18.0, 24.0),
        "luz": random.uniform(10.0, 14.0),
        "nivel": random.uniform(80.0, 100.0),
        "umidade": random.uniform(55.0, 65.0),
        "bomba_ligada": True,
    }


def atualizar_estado_fisico(estado: dict, com_anomalia: bool = False) -> dict:
    def drift(valor, variacao, minimo, maximo):
        valor += random.uniform(-variacao, variacao)
        return max(min(valor, maximo), minimo)

    if com_anomalia:
        estado["ph"] = random.choice([4.2, 7.8])
        estado["ec"] = random.choice([0.3, 3.2])
        estado["temp_agua"] = random.uniform(29.0, 34.0)
        estado["nivel"] = random.uniform(0.0, 15.0)
    else:
        estado["ph"] = drift(estado["ph"], 0.02, 5.5, 6.5)
        estado["ec"] = drift(estado["ec"], 0.05, 0.5, 2.5)
        estado["temp_ar"] = drift(estado["temp_ar"], 0.2, 15.0, 30.0)
        estado["temp_agua"] += (estado["temp_ar"] - estado["temp_agua"]) * 0.05
        estado["luz"] = drift(estado["luz"], 0.5, 8.0, 16.0)
        estado["umidade"] = drift(estado["umidade"], 0.5, 40.0, 90.0)

        if random.random() < 0.001:
            estado["bomba_ligada"] = not estado["bomba_ligada"]

        estado["nivel"] = 100.0 if estado["bomba_ligada"] else 0.0

    return estado


def gerar_telemetria_tupla(bancada_id: int, com_anomalia: bool = False) -> tuple:
    """
    Gera uma tupla exatamente com os 9 elementos esperados por inserir_leitura_sensor:
    (bancada_id, ph, ec, temperatura_ambiente, temperatura_agua, luminosidade, nivel_tanque, umidade, dth_recebido)
    """
    with _estado_lock:
        if bancada_id not in _estado_bancadas:
            _estado_bancadas[bancada_id] = inicializar_estado_bancada()
        st = atualizar_estado_fisico(_estado_bancadas[bancada_id], com_anomalia=com_anomalia)

    dth_agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return (
        int(bancada_id),
        round(st["ph"], 2),
        round(st["ec"], 2),
        round(st["temp_ar"], 2),
        round(st["temp_agua"], 2),
        round(st["luz"], 2),
        round(st["nivel"], 2),
        round(st["umidade"], 2),
        dth_agora,
    )