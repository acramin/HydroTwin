from __future__ import annotations

import pandas as pd

from hydrotwin.helpers.logger import logger

# =========================================================
# CONFIGURAÇÕES
# =========================================================

JANELA_ANALISE = 30

# variação mínima para considerar tendência
LIMIAR_VARIACAO = 0.05  # 5%


# =========================================================
# STATUS
# =========================================================

STATUS_SCORE = {
    "Estável": 0,
    "Subindo": 50,
    "Descendo": 50,
    "Mudança Brusca": 100,
}


# =========================================================
# FUNÇÕES AUXILIARES
# =========================================================

def _calcular_variacao(media_antiga, media_recente):
    if media_antiga is None or abs(media_antiga) < 1e-6:
        return 0.0

    return (media_recente - media_antiga) / abs(media_antiga)


def _classificar_tendencia(variacao):
    variacao_abs = abs(variacao)

    # praticamente parado
    if variacao_abs < LIMIAR_VARIACAO:
        return "Estável"

    # mudança muito forte
    if variacao_abs >= 0.20:
        return "Mudança Brusca"

    # tendência normal
    if variacao > 0:
        return "Subindo"

    return "Descendo"


def _gerar_mensagem(nome, tendencia, variacao_percentual, unidade):
    sufixo = f" {unidade}" if unidade else ""

    if tendencia == "Estável":
        return (
            f"{nome} permanece estável "
            f"com variação de {variacao_percentual:.1f}%."
        )

    if tendencia == "Mudança Brusca":
        return (
            f"{nome} apresentou mudança brusca "
            f"de {variacao_percentual:.1f}%."
        )

    return (
        f"{nome} apresenta tendência de "
        f"{tendencia.lower()} "
        f"({variacao_percentual:.1f}%)."
    )


# =========================================================
# FUNÇÃO PRINCIPAL
# =========================================================

def analisar_tendencias(df, janela=JANELA_ANALISE):
    """
    Analisa tendência simples comparando:
    média antiga vs média recente.
    """
    from hydrotwin.processing.default import METRICAS_CONFIG
    if df is None or df.empty:
        return {
            "status": "Sem dados",
            "score": 0,
            "total_tendencias": 0,
            "tendencias": [],
        }

    tendencias = []

    for sensor, config in METRICAS_CONFIG.items():
        # Excluir nivel_tanque (métrica categórica: 0=abaixo ou 100=normal)
        if sensor == "nivel_tanque":
            continue

        if sensor not in df.columns:
            continue

        serie = pd.to_numeric(df[sensor], errors="coerce").dropna()

        # precisa de pelo menos 2 janelas
        if len(serie) < janela * 2:
            continue

        # divide em duas partes
        serie_antiga = serie.iloc[-(janela * 2):-janela]
        serie_recente = serie.iloc[-janela:]

        media_antiga = float(serie_antiga.mean())
        media_recente = float(serie_recente.mean())

        variacao = _calcular_variacao(
            media_antiga=media_antiga,
            media_recente=media_recente,
        )

        tendencia = _classificar_tendencia(variacao)

        # ignora estável
        if tendencia == "Estável":
            continue

        unidade = config.get("unidade", "")
        nome = config.get("label", sensor)

        tendencias.append(
            {
                "sensor": sensor,
                "nome": nome,
                "status": tendencia,
                "score": STATUS_SCORE[tendencia],
                "media_antiga": round(media_antiga, 2),
                "media_recente": round(media_recente, 2),
                "variacao_percentual": round(variacao * 100, 1),
                "mensagem": _gerar_mensagem(
                    nome=nome,
                    tendencia=tendencia,
                    variacao_percentual=variacao * 100,
                    unidade=unidade,
                ),
            }
        )

    # -----------------------------------------------------
    # ORDENA POR MAIOR VARIAÇÃO
    # -----------------------------------------------------

    tendencias.sort(
        key=lambda item: abs(item["variacao_percentual"]),
        reverse=True,
    )

    # -----------------------------------------------------
    # STATUS GERAL
    # -----------------------------------------------------

    if not tendencias:
        return {
            "status": "Estável",
            "score": 0,
            "total_tendencias": 0,
            "tendencias": [],
        }

    score_geral = max(item["score"] for item in tendencias)

    if score_geral >= 100:
        status_geral = "Crítico"
    elif score_geral >= 50:
        status_geral = "Atenção"
    else:
        status_geral = "Estável"

    return {
        "status": status_geral,
        "score": score_geral,
        "total_tendencias": len(tendencias),
        "tendencias": tendencias,
    }