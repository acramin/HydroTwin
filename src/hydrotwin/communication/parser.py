
from hydrotwin.helpers.logger import logger
from datetime import datetime

# ================= PARSERS READER =================
def parse_linha(linha: str):
    try:
        partes = linha.strip().split(",")

        bancada_str = partes[0]  # Ex: "B1" ou "b1"
        ph = float(partes[1])
        ec = float(partes[2])
        temperatura_ambiente = float(partes[3])
        temperatura_agua = float(partes[4])
        luminosidade = float(partes[5])
        nivel_tanque = float(partes[6])
        umidade = float(partes[7])

        dth_recebido = datetime.now().isoformat()
        bancada_id = int(bancada_str.upper().replace("B", ""))

        return (
            bancada_id, ph, ec,
            temperatura_ambiente, temperatura_agua,
            luminosidade,
            nivel_tanque, umidade,
            dth_recebido
        )

    except (ValueError, IndexError) as e:
        logger.warning(f"Falha ao parsear linha de telemetria ('{linha}'): {e}")
        return None


def parsear_confirmacao_arduino(linha: str):
    try:
        partes = linha.strip().split(",")
        resposta_tipo = partes[0]

        if resposta_tipo not in ("PARAMS_OK", "PARAMS_ERROR"):
            return None

        campos = {}
        for parte in partes[1:]:
            if "=" in parte:
                chave, valor = parte.split("=", 1)
                campos[chave.strip()] = valor.strip()

        bancada_id = int(campos.get("bancada_id", -1))

        if resposta_tipo == "PARAMS_OK":
            return {"status": "ok", "bancada_id": bancada_id, "motivo": None}
        else:
            motivo = campos.get("motivo", "Erro desconhecido")
            return {"status": "erro", "bancada_id": bancada_id, "motivo": motivo}

    except Exception as e:
        logger.error(f"Erro ao parsear confirmação: {e}")
        return None

# ================= PARSERS SENDER =================
def formatar_mensagem_parametros(bancada_id: int, cultura_id: int, parametros: dict) -> str | None:
    """
    Formata mensagem para enviar parâmetros ao Arduino.
    Formato: PARAMS,bancada_id=X,cultura_id=Y,ph_min=...,ph_max=...,ec_min=...,ec_max=...,dias_ciclo=...
    """
    if not parametros:
        return None

    msg_parts = [
        "PARAMS",
        f"bancada_id={bancada_id}",
        f"cultura_id={cultura_id}",
        f"ph_min={parametros.get('ph_min', '')}",
        f"ph_max={parametros.get('ph_max', '')}",
        f"ec_min={parametros.get('ec_min', '')}",
        f"ec_max={parametros.get('ec_max', '')}",
        f"dias_ciclo={parametros.get('dias_ciclo', '')}",
    ]

    return ",".join(msg_parts) + "\n"