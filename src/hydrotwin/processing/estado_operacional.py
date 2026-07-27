from __future__ import annotations

from hydrotwin.helpers.logger import logger

# =========================================================
# FAIXAS OPERACIONAIS
# =========================================================

## Fallback caso não puxe do banco
LIMITES_OPERACIONAIS = {
    "ph": {
        "ideal": (5.5, 6.5),
        "atencao": (5.0, 7.0),
        "label": "pH",
        "unidade": "",
    },
    "ec": {
        "ideal": (1.2, 2.0),
        "atencao": (1.0, 2.3),
        "label": "Condutividade Elétrica",
        "unidade": "mS/cm",
    },
}

# =========================================================
# STATUS
# =========================================================

STATUS_SCORE = {
    "Saudável": 0,
    "Atenção": 50,
    "Crítico": 100,
    "Sem dados": 0,
}


# =========================================================
# FUNÇÕES AUXILIARES
# =========================================================

def _avaliar_faixa(valor, faixa_ideal, faixa_atencao):
    ideal_min, ideal_max = faixa_ideal
    atencao_min, atencao_max = faixa_atencao

    # dentro da faixa ideal
    if ideal_min <= valor <= ideal_max:
        return "Saudável"

    # dentro da faixa de atenção
    if atencao_min <= valor <= atencao_max:
        return "Atenção"

    # fora de tudo
    return "Crítico"


def _mensagem_sensor(nome, valor, unidade, status):
    sufixo = f" {unidade}" if unidade else ""

    if status == "Saudável":
        return f"{nome} em faixa ideal ({valor:.2f}{sufixo})."

    if status == "Atenção":
        return f"{nome} fora da faixa ideal ({valor:.2f}{sufixo})."

    return f"{nome} em condição crítica ({valor:.2f}{sufixo})."


# =========================================================
# FUNÇÃO PRINCIPAL
# =========================================================

def _construir_config_limites(limites_db: dict):
    """Converte o dicionário de limites (metrica -> (min, max)) vindo do banco
    para o formato esperado pela avaliação: {metrica: {"ideal":(...), "atencao":(...), "label":..., "unidade":...}}

    A faixa de atenção é derivada expandindo a faixa ideal em 20% por padrão.
    """
    from hydrotwin.processing.default import METRICAS_CONFIG
    config = {}
    for metrica, (lim_min, lim_max) in (limites_db or {}).items():
        meta = METRICAS_CONFIG.get(metrica, {})
        label = meta.get("label", metrica)
        unidade = meta.get("unidade", "")

        ideal = (lim_min, lim_max)

        atencao_min = None
        atencao_max = None
        if lim_min is not None and lim_max is not None:
            amplitude = max(lim_max - lim_min, 1e-6)
            delta = amplitude * 0.2
            atencao_min = lim_min - delta
            atencao_max = lim_max + delta
        else:
            # se estiver faltando um dos lados, repassa como None (não forçamos default)
            atencao_min = lim_min
            atencao_max = lim_max

        config[metrica] = {
            "ideal": ideal,
            "atencao": (atencao_min, atencao_max),
            "label": label,
            "unidade": unidade,
        }

    return config


def avaliar_estado_operacional(dados, limites: dict | None = None):
    """
    Avalia o estado operacional atual do sistema
    com base nas faixas ideais dos sensores críticos.
    """
    from hydrotwin.helpers import to_float
    if not dados:
        return {
            "status": "Sem dados",
            "score": 0,
            "sensores": {},
        }

    sensores = {}

    # Se foram fornecidos limites dinâmicos (vindo do DB), converte para o formato interno usado pela avaliação. 
    # Caso contrário, usa o conjunto hard-coded definido em `LIMITES_OPERACIONAIS`.
    if limites is not None:
        limites_config = _construir_config_limites(limites)
        logger.info("Usando limites dinâmicos do banco para avaliação:", limites_config)
    else:
        limites_config = LIMITES_OPERACIONAIS
        logger.info("Usando limites operacionais padrão para avaliação:", limites_config)

    for sensor, config in limites_config.items():
        valor = to_float(dados.get(sensor))

        if valor is None:
            continue

        status = _avaliar_faixa(
            valor=valor,
            faixa_ideal=config["ideal"],
            faixa_atencao=config["atencao"],
        )

        sensores[sensor] = {
            "nome": config["label"],
            "valor": round(valor, 2),
            "unidade": config["unidade"],
            "status": status,
            "score": STATUS_SCORE[status],
            "mensagem": _mensagem_sensor(
                nome=config["label"],
                valor=valor,
                unidade=config["unidade"],
                status=status,
            ),
        }

    # -----------------------------------------------------
    # STATUS GERAL
    # -----------------------------------------------------

    if not sensores:
        return {
            "status": "Sem dados",
            "score": 0,
            "sensores": {},
        }

    score_geral = max(sensor["score"] for sensor in sensores.values())

    if score_geral >= 100:
        status_geral = "Crítico"
    elif score_geral >= 50:
        status_geral = "Atenção"
    else:
        status_geral = "Saudável"

    return {
        "status": status_geral,
        "score": score_geral,
        "sensores": sensores,
    }