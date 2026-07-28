from datetime import datetime
from queue import Empty
import time

from hydrotwin.communication.events import (
    fila_confirmacao,
    fila_envio,
    ready_event,
    status_envios,
    status_envios_lock,
    stop_event,
)
from hydrotwin.db.crud.cultura import obter_parametros_cultura
from hydrotwin.helpers.logger import logger
from hydrotwin.communication.parser import formatar_mensagem_parametros

# ================= CONFIGURAÇÃO =================
CONFIRM_TIMEOUT = 10  # Tempo limite para resposta do hardware (segundos)


# ================= WORKER DE ENVIO =================
def atualizar_status(bancada_id: int, status: str, mensagem: str):
    """Atualiza o dicionário global de status de envio de forma thread-safe."""
    with status_envios_lock:
        status_envios[bancada_id] = {
            "status": status,
            "timestamp": datetime.now(),
            "mensagem": mensagem,
        }


def enviar_parametros_ideais_worker(transport):
    """Worker que processa a fila de envios e aguarda confirmação do Arduino."""
    logger.info("Worker de envio de parâmetros iniciado.")

    # Cache local para guardar confirmações recebidas fora de ordem
    confirmacoes_pendentes = {}

    while not stop_event.is_set():
        # Aguarda a conexão estar pronta
        if not ready_event.wait(timeout=1.0):
            continue

        try:
            bancada_id, cultura_id = fila_envio.get(timeout=1.0)
        except Empty:
            continue

        logger.info(f"Processando solicitação de envio -> Bancada: {bancada_id}, Cultura: {cultura_id}")
        atualizar_status(bancada_id, "enviando", "Enviando parâmetros ao Arduino...")

        parametros = obter_parametros_cultura(cultura_id)
        if not parametros:
            msg_erro = f"Cultura {cultura_id} não encontrada no banco de dados."
            logger.error(msg_erro)
            atualizar_status(bancada_id, "erro", msg_erro)
            continue

        mensagem = formatar_mensagem_parametros(bancada_id, cultura_id, parametros)

        try:
            logger.info(f"Enviando dados para Bancada {bancada_id}: {mensagem.strip()}")
            transport.enviar(mensagem)
        except Exception as e:
            msg_erro = f"Erro ao enviar pelo transporte: {e}"
            logger.error(msg_erro)
            atualizar_status(bancada_id, "erro", msg_erro)
            ready_event.clear()
            continue

        # Aguarda confirmação de recebimento do hardware
        confirmado = False
        limite_tempo = time.time() + CONFIRM_TIMEOUT

        # logger.info(f'Antes do While de confirmação!')
        # logger.info(f'Check 1 (tempo): {time.time() < limite_tempo}')
        # logger.info(f'Check 2 (event): {not stop_event.is_set()}')
        # logger.info(f'Check 3 (confirmado): {not confirmado}')

        while time.time() < limite_tempo and not stop_event.is_set() and not confirmado:
            logger.info(f'Inicio do While:')
            # 1. Verifica se já temos a resposta no cache local de fora de ordem
            if bancada_id in confirmacoes_pendentes:
                # logger.info(f'Temos confirmacoes pendentes!')
                confirmacao = confirmacoes_pendentes.pop(bancada_id)
            else:
                try:
                    confirmacao = fila_confirmacao.get(timeout=1.0)
                    # logger.info(f'Bloco de fila_confirmacao: {confirmacao}')
                except Empty:
                    # logger.info('Fila de confirmacao vazia')
                    continue
            
            
            # 2. Se a confirmação for de outra bancada, guarda no cache local para não perder
            c_bancada = confirmacao.get("bancada_id")
            if c_bancada != bancada_id:
                # logger.info(f'Adiciona pendencia de confirmacao!')
                confirmacoes_pendentes[c_bancada] = confirmacao
                continue

            # 3. Processa a confirmação pertencente à bancada atual
            if confirmacao.get("status") == "ok":
                atualizar_status(bancada_id, "sucesso", "Parâmetros recebidos com sucesso pelo Arduino.")
                logger.info(f"Confirmação 'OK' recebida para a bancada {bancada_id}.")
            else:
                motivo = confirmacao.get("motivo", "Erro desconhecido")
                atualizar_status(bancada_id, "erro", f"Erro retornado pelo Arduino: {motivo}")
                logger.warning(f"Arduino rejeitou os parâmetros para bancada {bancada_id}: {motivo}")

            confirmado = True

        if not confirmado and not stop_event.is_set():
            msg_timeout = f"Timeout ({CONFIRM_TIMEOUT}s) aguardando confirmação do Arduino."
            logger.warning(f"Bancada {bancada_id}: {msg_timeout}")
            atualizar_status(bancada_id, "erro", msg_timeout)

    logger.info("Worker de envio de parâmetros encerrado.")
