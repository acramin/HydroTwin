from __future__ import annotations

from typing import Any
import pandas as pd
from hydrotwin import (
    formatar_data,
    get_bancadas,
    get_sensor_proc_ultimo,
    get_alertas_ativos,
    get_raw_recent,
    logger
)

def get_last_status() -> dict[str, dict[str, Any]]:
    """Retorna o status atual e a data de atualização aninhados por bancada."""
    logger.debug("get_last_status() -> dict[str, dict[str, Any]]")
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
    logger.debug("get_kpis(bancada_id: int | str) -> dict[str, Any]")
    df = get_raw_recent(bancada_id)
    
    if df is None:
        df = pd.DataFrame()
        
    if not df.empty:
        df = df.copy()
        df["dth_recebido"] = pd.to_datetime(df["dth_recebido"], errors="coerce")
        df = df.dropna(subset=["dth_recebido"]).sort_values("dth_recebido")
        leitura = df.loc[df.index[-1]]
        #logger.debug(f"{leitura.ph}")
    
    nivel_atual = leitura.nivel_tanque
    status_tanque = "Normal" if (nivel_atual is not None and nivel_atual == 0 ) else "Abaixo"

    return {
        "nivel_tanque": status_tanque,
        "ph": leitura.ph,
        "ec": leitura.ec,
        "umidade": leitura.umidade,
        "temperatura_ambiente": leitura.temperatura_ambiente,
        "temperatura_agua": leitura.temperatura_agua,
        "luminosidade": leitura.luminosidade,
    }


def get_alertas() -> list[dict[str, Any]]:
    """Retorna alertas ativos estruturados para facilitar renderização no frontend."""
    logger.debug("get_alertas() -> list[dict[str, Any]]")
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