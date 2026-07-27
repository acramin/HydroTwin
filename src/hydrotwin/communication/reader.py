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

# ================= ESTADO GLOBAL =================
INTERVALO_PROCESSAMENTO_S = 30  # Em segundos; tempo aumenta para 3600 (1 hora) no sistema real
TIMEOUT_COMUNICACAO = 1200      # 20 minutos; dados devem chegar a cada 15 minutos no sistema real

comunicacao_offline = False

# ================= DB WRITER =================
def db_writer():
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

            logger.debug(f"Salvo no banco: {dados}")

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


# ================= PARSERS =================
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


# ================= TRANSPORT READER =================
def transport_reader(transport):
    global ultimo_recebimento
    logger.info("Transport Reader iniciado.")

    while not stop_event.is_set():
        try:
            linha = transport.receber()

            if linha:
                logger.debug(f"Recebido raw: {linha.strip()}")

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
                else:
                    logger.warning(f"Linha ignorada (formato inválido): {linha.strip()}")

            # CENTRALIZADO: Executa sempre no final de cada ciclo do loop
            time.sleep(0.1)

        except Exception as e:
            logger.error(f"Erro no transporte (conexão perdida): {e}")

            ready_event.clear()
            try:
                transport.fechar()
            except Exception:
                pass

            reconectado = False
            for tentativa in range(1, 6):
                if stop_event.is_set():
                    break

                try:
                    logger.info(f"Tentando reconectar transporte... ({tentativa}/5)")
                    transport.conectar()
                    reconectado = True
                    logger.info("Transporte reconectado com sucesso.")
                    ready_event.set()
                    break
                except Exception as e2:
                    logger.error(f"Reconexão falhou: {e2}")
                    time.sleep(2)

            if not reconectado:
                logger.critical("Não foi possível reconectar após 5 tentativas. Encerrando.")
                stop_event.set()
                break
    time.sleep(0.1)        

    try:
        transport.fechar()
    except Exception:
        pass

    logger.info("Transport Reader encerrado.")


# ================= MONITOR =================
def monitor_comunicacao():
    global comunicacao_offline
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