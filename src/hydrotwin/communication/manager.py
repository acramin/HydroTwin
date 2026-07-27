import threading
import time

from hydrotwin.helpers.env import get_transport_mode
from hydrotwin.transport import SerialTransport, TCPServerTransport
from hydrotwin.helpers.logger import logger

# Importações com fallback para execução direta ou via módulo
try:
    from .reader import (
        db_writer,
        loop_processamento_periodico,
        monitor_comunicacao,
        transport_reader,
    )
    from .sender import enviar_parametros_ideais_worker
except ImportError:
    from hydrotwin.communication.reader import (
        db_writer,
        loop_processamento_periodico,
        monitor_comunicacao,
        transport_reader,
    )
    from hydrotwin.communication.sender import enviar_parametros_ideais_worker
except ImportError as e:
    logger.critical(f'Erro de importação no manager: {e}')

# ================ CONFIG =================
PORTA = '/dev/ttyACM0'
BAUD_RATE = 9600

HOST = '0.0.0.0'
PORT = 65432

# ================= GLOBAL STATE =================

from hydrotwin.communication.events import stop_event, ready_event

def encerrar_sistema(transport, threads):
    """Centraliza o desligamento gracioso dos recursos e threads."""
    if stop_event.is_set() and not ready_event.is_set():
        # Evita execuções de encerramento redundantes
        pass

    logger.info("Iniciando processo de encerramento...")
    stop_event.set()

    if transport:
        try:
            transport.fechar()
            logger.info("Transporte de comunicação fechado.")
        except Exception as e:
            logger.error(f"Erro ao fechar transporte: {e}")

    # Aguarda a finalização das threads ativas
    for t in threads:
        if t.is_alive() and t != threading.current_thread():
            t.join(timeout=1.0)

    logger.info("Sistema encerrado com sucesso.")


def conexao_worker(transport):
    """Worker focado exclusivamente na abertura do transporte."""
    try:
        logger.info("Aguardando conexão do hardware/cliente...")
        transport.conectar()
        logger.info("Conexão estabelecida com sucesso!")
        ready_event.set()
    except Exception as e:
        logger.critical(f"Erro crítico ao estabelecer conexão: {e}")
        stop_event.set()


def worker_com_barreira(target_func, *args):
    """Aguardará a conexão ficar pronta usando o tempo de bloqueio nativo do Event."""
    while not stop_event.is_set():
        # O wait() bloqueia a thread de forma eficiente até ready_event ser setado
        if ready_event.wait(timeout=0.5):
            target_func(*args)
            break


def main():
    transport_mode = get_transport_mode()
    
    if transport_mode == 'serial':
        transport = SerialTransport(PORTA, BAUD_RATE)
    else:
        transport = TCPServerTransport(HOST, PORT)

    threads = []

    # Configuração das Threads
    t_conectar = threading.Thread(
        target=conexao_worker, args=(transport,), name="ConexaoWorker", daemon=True
    )
    t_reader = threading.Thread(
        target=worker_com_barreira, args=(transport_reader, transport), name="ReaderWorker", daemon=True
    )
    t_sender = threading.Thread(
        target=worker_com_barreira, args=(enviar_parametros_ideais_worker, transport), name="SenderWorker", daemon=True
    )
    t_db = threading.Thread(
        target=worker_com_barreira, args=(db_writer,), name="DBWriterWorker", daemon=True
    )
    t_proc = threading.Thread(
        target=worker_com_barreira, args=(loop_processamento_periodico,), name="ProcWorker", daemon=True
    )
    t_monitor = threading.Thread(
        target=worker_com_barreira, args=(monitor_comunicacao,), name="MonitorWorker", daemon=True
    )

    threads.extend([t_conectar, t_reader, t_sender, t_db, t_proc, t_monitor])

    # Inicialização
    for t in threads:
        t.start()

    logger.info("Sistema inicializado. Aguardando prontidão da conexão...")

    try:
        # Loop principal apenas monitora a interrupção da aplicação
        while not stop_event.is_set():
            time.sleep(0.5)
            
    except KeyboardInterrupt:
        logger.info("Interrupção solicitada pelo usuário (Ctrl+C).")
    finally:
        encerrar_sistema(transport, threads)


if __name__ == "__main__":
    main()