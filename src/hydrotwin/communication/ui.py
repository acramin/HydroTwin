from queue import Full
from hydrotwin.communication.events import (
    fila_envio,
    status_envios,
    status_envios_lock,
)
from hydrotwin.helpers.logger import logger


def enfileirar_envio(bancada_id: int, cultura_id: int) -> bool:
    """Enfileira o envio dos parâmetros de uma bancada para processamento."""
    logger.debug("enfileirar_envio(bancada_id: int, cultura_id: int) -> bool")
    try:
        fila_envio.put((bancada_id, cultura_id), timeout=1.0)
        logger.info(f"Envio enfileirado: Bancada={bancada_id}, Cultura={cultura_id}")
        return True
    except Full:
        logger.error("Fila de envio cheia. Não foi possível enfileirar o comando.")
        return False
    except Exception as e:
        logger.error(f"Erro ao enfileirar envio: {e}")
        return False


def obter_status_envio(bancada_id: int) -> dict:
    """Retorna o status atual do envio para uma bancada específica."""
    logger.debug("obter_status_envio(bancada_id: int) -> dict")
    with status_envios_lock:
        if bancada_id in status_envios:
            return status_envios[bancada_id].copy()

    return {
        "status": "nao_iniciado",
        "timestamp": None,
        "mensagem": "Envio ainda não foi iniciado."
    }

def limpar_status_envio(bancada_id: int):
    """Remove o registro de status de uma bancada após a consulta pelo frontend."""
    logger.debug("limpar_status_envio(bancada_id: int)")
    with status_envios_lock:
        status_envios.pop(bancada_id, None)