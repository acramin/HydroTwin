
from hydrotwin.helpers.logger import logger
from datetime import datetime

# ================= PARSERS READER =================
def parse_linha(linha: str):
    try:
        partes = linha.strip().split(",")

        # Pega apenas o que vem antes dos dois pontos (ex: "B1:ARDUINO_01" -> "B1")
        bancada_str = partes[0].split(":")[0]
        
        ph = float(partes[1])
        ec = float(partes[2])
        temperatura_ambiente = float(partes[3])
        umidade = float(partes[4])
        temperatura_agua = float(partes[5])
        luminosidade = float(partes[6])
        nivel_tanque = float(partes[7])
        

        dth_recebido = datetime.now().isoformat()
        
        # Converte "B1" ou "b1" para o inteiro 1
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

def parser_arduino_id(linha : str):
    from hydrotwin.db.crud.controlador import criar_controlador
    try:
        partes = linha.strip().split(",")
        
        nome_arduino = partes[1]
        
        arduino_id = criar_controlador(nome_arduino)
        
        return arduino_id
        
    except (ValueError, IndexError) as e:
        logger.warning(f"Falha ao parsear linha de cadastro controlador ('{linha}'): {e}")
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
        f"tempo_luz_acesa={parametros.get('tempo_luz_acesa', '')}",
        f"lux_min={parametros.get('lux_min', '')}",
        f"lux_max={parametros.get('lux_max', '')}",
    ]

    return ",".join(msg_parts) + "\n"
