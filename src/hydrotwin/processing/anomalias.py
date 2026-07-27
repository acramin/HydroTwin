from __future__ import annotations

import pandas as pd

# =========================================================
# CONFIGURAÇÕES
# =========================================================

JANELA_ANALISE = 30

LIMIARES = {
    "Saudável": 0.10,   # até 10%
    "Atenção": 0.20,    # até 20%
}


# =========================================================
# STATUS
# =========================================================

STATUS_SCORE = {
    "Saudável": 0,
    "Atenção": 50,
    "Crítico": 100,
}


# =========================================================
# FUNÇÕES AUXILIARES
# =========================================================

def _calcular_desvio_percentual(valor_atual, media):
    if media is None or abs(media) < 1e-6:
        return 0.0

    return abs(valor_atual - media) / abs(media)


def _classificar_desvio(desvio):
    if desvio <= LIMIARES["Saudável"]:
        return "Saudável"

    if desvio <= LIMIARES["Atenção"]:
        return "Atenção"

    return "Crítico"


def _gerar_mensagem(nome, valor, media, desvio_percentual, unidade, status):
    sufixo = f" {unidade}" if unidade else ""

    return (
        f"{nome} apresentou desvio de "
        f"{desvio_percentual:.1f}% em relação à média recente. "
        f"Valor atual: {valor:.2f}{sufixo}. "
        f"Média recente: {media:.2f}{sufixo}. "
        f"Status: {status}."
    )


# =========================================================
# FUNÇÃO PRINCIPAL
# =========================================================

def detectar_anomalias(df, janela=JANELA_ANALISE):
    """
    Detecta mudanças bruscas comparando
    o valor atual com a média recente.
    """

    from hydrotwin.processing.default import METRICAS_CONFIG

    if df is None or df.empty:
        return {
            "status": "Sem dados",
            "score": 0,
            "total_anomalias": 0,
            "anomalias": [],
        }

    anomalias = []

    for sensor, config in METRICAS_CONFIG.items():
        # Excluir nivel_tanque (métrica categórica: 0=abaixo ou 100=normal)
        if sensor == "nivel_tanque":
            continue

        if sensor not in df.columns:
            continue

        serie = pd.to_numeric(df[sensor], errors="coerce").dropna()

        if len(serie) < janela:
            continue

        serie_recente = serie.tail(janela)

        valor_atual = float(serie_recente.iloc[-1])

        media_recente = float(serie_recente.iloc[:-1].mean())

        desvio = _calcular_desvio_percentual(
            valor_atual=valor_atual,
            media=media_recente,
        )

        status = _classificar_desvio(desvio)

        # ignora sensores saudáveis
        if status == "Saudável":
            continue

        unidade = config.get("unidade", "")
        nome = config.get("label", sensor)

        anomalias.append(
            {
                "sensor": sensor,
                "nome": nome,
                "status": status,
                "score": STATUS_SCORE[status],
                "valor_atual": round(valor_atual, 2),
                "media_recente": round(media_recente, 2),
                "desvio_percentual": round(desvio * 100, 1),
                "mensagem": _gerar_mensagem(
                    nome=nome,
                    valor=valor_atual,
                    media=media_recente,
                    desvio_percentual=desvio * 100,
                    unidade=unidade,
                    status=status,
                ),
            }
        )

    # -----------------------------------------------------
    # ORDENA POR GRAVIDADE
    # -----------------------------------------------------

    anomalias.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    # -----------------------------------------------------
    # STATUS GERAL
    # -----------------------------------------------------

    if not anomalias:
        return {
            "status": "Saudável",
            "score": 0,
            "total_anomalias": 0,
            "anomalias": [],
        }

    score_geral = max(item["score"] for item in anomalias)

    if score_geral >= 100:
        status_geral = "Crítico"
    elif score_geral >= 50:
        status_geral = "Atenção"
    else:
        status_geral = "Saudável"

    return {
        "status": status_geral,
        "score": score_geral,
        "total_anomalias": len(anomalias),
        "anomalias": anomalias,
    }