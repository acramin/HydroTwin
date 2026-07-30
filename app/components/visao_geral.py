from __future__ import annotations

from typing import Any
from hydrotwin import (
    formatar_data,
    get_bancadas,
    get_sensor_proc_ultimo,
    get_alertas_ativos,
)

def get_last_status() -> dict[str, dict[str, Any]]:
    """Retorna o status atual e a data de atualização aninhados por bancada."""
    status_bancadas = {}
    bancadas = get_bancadas() or []

    for bancada in bancadas:
        if not bancada or not bancada[0]:
            continue

        bancada_id, nome = bancada[0], bancada[1]
        leitura = get_sensor_proc_ultimo(bancada_id)

        if leitura:
            status_bancadas[nome] = {
                "status": leitura.get("status_exibicao", "Sem dados"),
                "atualizado_em": formatar_data(leitura.get("dth_calculado")),
            }
        else:
            status_bancadas[nome] = {
                "status": "Sem dados",
                "atualizado_em": "N/A",
            }

    return status_bancadas


def get_kpis(bancada_id: int | str) -> dict[str, Any]:
    """Retorna o dicionário de KPIs recentes para uma bancada específica."""
    leitura = get_sensor_proc_ultimo(bancada_id)
    if not leitura:
        return {}

    # nivel_tanque é categórico: <= 50 é Normal, > 50 é Abaixo
    nivel_mean = leitura.get("nivel_tanque_mean")
    status_nivel = (
        "Normal" if (nivel_mean is not None and nivel_mean <= 50) else "Abaixo"
    )

    return {
        "nivel_tanque": status_nivel,
        "ph": leitura.get("ph_mean"),
        "ec": leitura.get("ec_mean"),
        "umidade": leitura.get("umidade_mean"),
        "temperatura_ambiente": leitura.get("temperatura_ambiente_mean"),
        "temperatura_agua": leitura.get("temperatura_agua_mean"),
        "luminosidade": leitura.get("luminosidade_mean"),
    }


def get_alertas() -> list[dict[str, Any]]:
    """Retorna alertas ativos estruturados para facilitar renderização no frontend."""
    alertas = []
    bancadas = get_bancadas() or []

    for bancada in bancadas:
        if not bancada or not bancada[0]:
            continue

        bancada_id, nome = bancada[0], bancada[1]
        alertas_bancada = get_alertas_ativos(bancada_id) or []

        for alerta in alertas_bancada:
            mensagem = alerta.get("mensagem", "Alerta sem descrição")
            alertas.append({
                "bancada": nome,
                "bancada_id": bancada_id,
                "mensagem": mensagem,
                "nivel": alerta.get("nivel", "atencao"),
                "texto_formatado": f"{nome}: {mensagem}",
            })

    return alertas