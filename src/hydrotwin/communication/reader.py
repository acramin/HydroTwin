from datetime import datetime
from queue import Empty, Full
import time

from hydrotwin.helpers.logger import logger
from hydrotwin.communication.events import (
    bancadas_ativas,
    bancadas_lock,
    fila_confirmacao,
    fila_dados,
    ready_event,
    stop_event,
    ultimo_recebimento,
    ultimo_recebimento_lock,
)
from hydrotwin.db import conectar_db
from hydrotwin.db.crud.sensor import processar_sensor as processar_sensor_db, inserir_leitura_sensor
from hydrotwin.communication.parser import parse_linha, parsear_confirmacao_arduino, parser_arduino_id

# ================= ESTADO GLOBAL =================
INTERVALO_PROCESSAMENTO_S = 30  # Em segundos; tempo aumenta para 3600 (1 hora) no sistema real
TIMEOUT_COMUNICACAO = 1200      # 20 minutos; dados devem chegar a cada 15 minutos no sistema real

comunicacao_offline = False

# ================= DB WRITER =================
def db_writer():
    logger.debug("db_writer()")
    conn = conectar_db()

    logger.info("DB Writer iniciado.")

    while not stop_event.is_set() or not fila_dados.empty():
        # Reconexão resiliente
        if conn is None:
            logger.warning("DB Writer tentando reconectar ao banco de dados...")
            try:
                conn = conectar_db()
                logger.info("Conexão com o banco restabelecida.")
            except Exception as e:
                logger.error(f"Falha ao reconectar ao banco: {e}. Aguardando...")
                time.sleep(2)
                continue

        # Leitura da Fila
        try:
            dados = fila_dados.get(timeout=1)
        except Empty:
            continue

        # Processamento e Chamada do CRUD
        try:
            bancada_id = inserir_leitura_sensor(conn, dados)

            with bancadas_lock:
                bancadas_ativas.add(bancada_id)

            #logger.debug(f"Salvo no banco: {dados}")

        except Exception as e:
            logger.error(f"Erro ao salvar no banco (realizando rollback): {e}")
            if conn:
                try:
                    conn.rollback()
                except Exception:
                    pass

            # Detecta se a conexão caiu para forçar reconexão na próxima volta
            if any(k in str(e).lower() for k in ("connection", "closed", "lost")):
                try:
                    conn.close()
                except Exception:
                    pass
                conn = None

    if conn:
        try:
            conn.close()
        except Exception:
            pass

    logger.info("DB Writer encerrado.")


# ================= PROCESSAMENTO =================
def loop_processamento_periodico():
    logger.debug("loop_processamento_periodico()")
    logger.info("Loop de processamento periódico iniciado.")

    while not stop_event.is_set():
        # Aguarda o intervalo de processamento de forma otimizada
        if stop_event.wait(timeout=INTERVALO_PROCESSAMENTO_S):
            break

        with bancadas_lock:
            bancadas_para_processar = list(bancadas_ativas)
            if bancadas_para_processar:
                bancadas_ativas.clear()

        if not bancadas_para_processar:
            logger.debug("Sem dados novos de bancadas ativas, pulando processamento.")
            continue

        for bancada_id in bancadas_para_processar:
            try:
                processar_sensor_db(
                    bancada_id,
                    janela_horaria="1h",
                    horas=3600,
                )
                logger.info(f"Processamento concluído para bancada {bancada_id}")
            except Exception as e:
                logger.error(f"Erro ao processar bancada {bancada_id}: {e}")
                # Devolve a bancada para a fila de reprocessamento em caso de erro
                with bancadas_lock:
                    bancadas_ativas.add(bancada_id)

    logger.info("Loop de processamento periódico encerrado.")

# ================= TRANSPORT READER =================
def transport_reader(transport):
    global ultimo_recebimento
    logger.debug("transport_reader(transport)")
    logger.info("Transport Reader iniciado.")

    while not stop_event.is_set():
        # Aguarda a conexão estar pronta antes de tentar ler
        if not ready_event.wait(timeout=0.5):
            continue
        
        try:
            linha = transport.receber()

            if linha:
                confirmacao = parsear_confirmacao_arduino(linha)
                
                if confirmacao:
                    try:
                        fila_confirmacao.put(confirmacao, timeout=1)
                        logger.info(f"Confirmação enfileirada: {confirmacao}")
                    except Full:
                        logger.warning("Fila de confirmação cheia.")
                        
                elif linha.startswith(("B", "b")) and linha.count(",") >= 7:
                    dados_parseados = parse_linha(linha)
                    if dados_parseados:
                        with ultimo_recebimento_lock:
                            ultimo_recebimento = datetime.now()

                        try:
                            fila_dados.put(dados_parseados, timeout=1)
                        except Full:
                            logger.warning("Fila de dados cheia!")

                elif linha.startswith("INIT_NODE"):
                    arduino_id = parser_arduino_id(linha)
                    logger.info(f"Arduino cadastrado! id:{arduino_id}")
                elif linha.startswith(("DEBUG", "---")):
                    logger.debug(f"Arduino: {linha.strip()}")

                else:
                    logger.warning(f"Linha ignorada (formato inválido): {linha.strip()}")

            time.sleep(0.1)

        except Exception as e:
            # Em caso de queda de conexão: apenas avisa, fecha o transporte e invalida o evento
            logger.warning(f"Conexão perdida durante a leitura: {e}")
            ready_event.clear()        
            try:
                transport.fechar()
            except Exception:
                pass

    # Limpeza ao encerrar a aplicação completamente
    try:
        transport.fechar()
    except Exception:
        pass

    logger.info("Transport Reader encerrado.")

# ================= MONITOR =================
def monitor_comunicacao():
    global comunicacao_offline
    logger.debug("monitor_comunicacao()")
    logger.info("Monitor de comunicação iniciado.")

    while not stop_event.is_set():
        agora = datetime.now()

        with ultimo_recebimento_lock:
            snapshot_ultimo_recebimento = ultimo_recebimento

        segundos_sem_dados = (agora - snapshot_ultimo_recebimento).total_seconds()
        
        # logger.debug(f"Check 1 (time - off): {segundos_sem_dados > TIMEOUT_COMUNICACAO}")
        # logger.debug(f"Check 2 (var - off): {not comunicacao_offline}")
        # logger.debug(f"Check 3 (time - on): {segundos_sem_dados <= TIMEOUT_COMUNICACAO}")
        # logger.debug(f"Check 2 (var - on): {comunicacao_offline}")

        if segundos_sem_dados > TIMEOUT_COMUNICACAO and not comunicacao_offline:
            comunicacao_offline = True
            logger.warning(f"ALERTA: Sem comunicação há {segundos_sem_dados:.0f}s")


        elif segundos_sem_dados <= TIMEOUT_COMUNICACAO and comunicacao_offline:
            logger.info("Comunicação restabelecida.")
            comunicacao_offline = False

        # Aguarda 60 segundos antes de checar novamente
        if stop_event.wait(timeout=60):
            break

    logger.info("Monitor de comunicação encerrado.")