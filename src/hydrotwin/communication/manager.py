import threading
import time
import sys

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
    """Worker dedicado exclusivamente a estabelecer e manter a conexão ativa."""
    tentativas = 0
    INTERVALO_RECONEXAO = 2  # segundos

    while not stop_event.is_set():
        # Se a conexão foi perdida (ready_event limpo pelo transport_reader)
        if not ready_event.is_set():
            try:
                tentativas += 1
                logger.info(f"Tentando conectar/reconectar transporte... (Tentativa {tentativas})")
                
                # Fecha conexões antigas pendentes por segurança
                try:
                    transport.fechar()
                except Exception:
                    pass

                transport.conectar()
                
                logger.info("Conexão estabelecida com sucesso!")
                tentativas = 0
                ready_event.set()  # Notifica o transport_reader para voltar a ler!

            except Exception as e:
                logger.warning(f"Reconexão falhou: {e}. Retentando em {INTERVALO_RECONEXAO}s...")
                
                # Se tentar por muito tempo sem sucesso (ex: 50 tentativas = 100s)
                if tentativas >= 50:
                    logger.critical("Impossível restabelecer conexão após várias tentativas. Encerrando.")
                    stop_event.set()
                    break

                time.sleep(INTERVALO_RECONEXAO)
        else:
            # Se já está conectado, dorme um pouco para não ocupar CPU
            time.sleep(0.5)


def worker_com_barreira(target_func, *args):
    """Aguardará a conexão ficar pronta e tratará quedas de conexão."""
    while not stop_event.is_set():
        # Aguarda a conexão ficar pronta (ready_event)
        if ready_event.wait(timeout=1.0):
            try:
                target_func(*args)
            except Exception as e:
                logger.error(f"Erro na execução da worker {target_func.__name__}: {e}")
                # Se o erro for de desconexão, limpa o ready_event para pausar as workers
                ready_event.clear()


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
        
        # Se saiu porque deu um erro (não por Ctrl+C do usuário):
        if stop_event.is_set():
            sys.exit(1) # Avisa o Linux/systemd que foi um encerramento por ERRO


if __name__ == "__main__":
    main()
