from datetime import datetime, timedelta
from queue import Empty, Full
from unittest.mock import MagicMock, call, patch
import pytest

# Altere 'hydrotwin.reader' para o caminho relativo ou absoluto do seu ficheiro
NOME_DO_MODULO = "hydrotwin.communication.reader"

from hydrotwin.communication.reader import (
    INTERVALO_PROCESSAMENTO_S,
    TIMEOUT_COMUNICACAO,
    db_writer,
    loop_processamento_periodico,
    monitor_comunicacao,
    parse_linha,
    parsear_confirmacao_arduino,
    transport_reader,
)

# ==============================================================================
# FIXTURES E RESET DE ESTADO GLOBAL
# ==============================================================================

@pytest.fixture(autouse=True)
def reset_global_state(monkeypatch):
    """
    Limpa e reinicializa todas as variáveis globais, filas e eventos antes
    e depois de cada teste para garantir isolamento completo.
    """
    # Importa os eventos e filas reais para limpeza
    from hydrotwin.communication import events

    events.stop_event.clear()
    events.ready_event.clear()

    # Esvazia filas
    while not events.fila_dados.empty():
        try:
            events.fila_dados.get_nowait()
        except Empty:
            break

    while not events.fila_confirmacao.empty():
        try:
            events.fila_confirmacao.get_nowait()
        except Empty:
            break

    with events.bancadas_lock:
        events.bancadas_ativas.clear()

    with events.ultimo_recebimento_lock:
        events.ultimo_recebimento = datetime.now()

    # Reset da flag de estado offline do módulo reader
    monkeypatch.setattr(f"{NOME_DO_MODULO}.comunicacao_offline", False)

    yield

    events.stop_event.clear()
    events.ready_event.clear()


# ==============================================================================
# TESTES: PARSERS
# ==============================================================================

class TestParsers:

    def test_parse_linha_valida(self, monkeypatch):
        """Testa o parseamento de uma linha de telemetria válida."""
        agora_fixo = datetime(2026, 7, 26, 14, 0, 0)

        class DummyDatetime(datetime):
            @classmethod
            def now(cls, tz=None):
                return agora_fixo

        monkeypatch.setattr(f"{NOME_DO_MODULO}.datetime", DummyDatetime)

        linha = "B1,6.8,1.4,25.5,22.0,600.0,80.0,55.0"
        resultado = parse_linha(linha)

        assert resultado is not None
        assert resultado[0] == 1  # bancada_id
        assert resultado[1] == 6.8  # ph
        assert resultado[2] == 1.4  # ec
        assert resultado[3] == 25.5  # temp_ambiente
        assert resultado[4] == 22.0  # temp_agua
        assert resultado[5] == 600.0  # luminosidade
        assert resultado[6] == 80.0  # nivel_tanque
        assert resultado[7] == 55.0  # umidade
        assert resultado[8] == agora_fixo.isoformat()

    def test_parse_linha_com_bancada_minuscula(self):
        """Valida se o identificador de bancada 'b2' é corretamente convertido para int 2."""
        linha = "b2,7.0,1.2,24.0,21.0,500.0,75.0,60.0"
        resultado = parse_linha(linha)

        assert resultado is not None
        assert resultado[0] == 2

    def test_parse_linha_invalida_retorna_none(self):
        """Garante que dados malformados ou incompletos retornam None."""
        assert parse_linha("B1,6.8,invalido,25.5") is None
        assert parse_linha("texto_aleatorio") is None

    def test_parsear_confirmacao_arduino_ok(self):
        """Valida resposta de confirmação PARAMS_OK."""
        linha = "PARAMS_OK,bancada_id=3"
        resultado = parsear_confirmacao_arduino(linha)

        assert resultado == {
            "status": "ok",
            "bancada_id": 3,
            "motivo": None
        }

    def test_parsear_confirmacao_arduino_erro(self):
        """Valida resposta de confirmação PARAMS_ERROR com motivo especificado."""
        linha = "PARAMS_ERROR,bancada_id=2,motivo=Valor fora da faixa"
        resultado = parsear_confirmacao_arduino(linha)

        assert resultado == {
            "status": "erro",
            "bancada_id": 2,
            "motivo": "Valor fora da faixa"
        }

    def test_parsear_confirmacao_tipo_desconhecido(self):
        """Linhas que não sejam PARAMS_OK ou PARAMS_ERROR devem retornar None."""
        assert parsear_confirmacao_arduino("OUTRO_STATUS,bancada_id=1") is None
        assert parsear_confirmacao_arduino("linha_invalida") is None


# ==============================================================================
# TESTES: DB WRITER
# ==============================================================================

class TestDBWriter:

    @patch(f"{NOME_DO_MODULO}.conectar_db")
    def test_db_writer_fluxo_sucesso(self, mock_conectar_db):
        """Testa o processamento normal de inserção na base de dados."""
        from hydrotwin.communication.events import bancadas_ativas, fila_dados, stop_event

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_conectar_db.return_value = mock_conn

        # Insere um elemento na fila e sinaliza parada do stop_event em seguida
        dados_exemplo = (1, 7.0, 1.2, 25.0, 22.0, 500.0, 80.0, 60.0, "2026-07-26T14:00:00")
        fila_dados.put(dados_exemplo)
        stop_event.set()

        db_writer()

        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()
        assert 1 in bancadas_ativas
        mock_conn.close.assert_called_once()

    @patch(f"{NOME_DO_MODULO}.conectar_db")
    def test_db_writer_reconectando_banco_nulo(self, mock_conectar_db):
        """Testa tentativa de reconexão quando a conexão inicial com a base de dados falha."""
        from hydrotwin.communication.events import stop_event

        # 1. Garante que o worker VAI ENTRAR no loop while
        stop_event.clear()

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor

        # 2. Define o comportamento da reconexão
        def side_effect_conectar():
            if mock_conectar_db.call_count == 1:
                return None  # 1ª tentativa falha
            
            # Na 2ª tentativa (reconexão dentro do while), manda o worker parar
            stop_event.set()
            return mock_conn

        mock_conectar_db.side_effect = side_effect_conectar

        # 3. Executa a função
        db_writer()

        # 4. Asserts
        assert mock_conectar_db.call_count == 2
        mock_conn.close.assert_called_once()

    @patch(f"{NOME_DO_MODULO}.conectar_db")
    def test_db_writer_rollback_em_erro_de_execucao(self, mock_conectar_db):
        """Garante a execução de rollback em caso de falha de gravação SQL."""
        from hydrotwin.communication.events import fila_dados, stop_event

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = Exception("Erro de chave duplicada")
        mock_conn.cursor.return_value = mock_cursor
        mock_conectar_db.return_value = mock_conn

        dados_exemplo = (1, 7.0, 1.2, 25.0, 22.0, 500.0, 80.0, 60.0, "2026-07-26T14:00:00")
        fila_dados.put(dados_exemplo)
        stop_event.set()

        db_writer()

        mock_conn.rollback.assert_called_once()


# ==============================================================================
# TESTES: PROCESSAMENTO PERIÓDICO
# ==============================================================================

class TestLoopProcessamentoPeriodico:

    @patch(f"{NOME_DO_MODULO}.processar_sensor_db")
    def test_processamento_sucesso(self, mock_processar_db, monkeypatch):
        """Valida o processamento bem-sucedido das bancadas ativas."""
        from hydrotwin.communication.events import bancadas_ativas, stop_event

        # 1. Garante o estado inicial limpo
        stop_event.clear()
        bancadas_ativas.clear()

        bancadas_ativas.add(1)
        bancadas_ativas.add(2)

        # 2. Na 1ª iteração retorna False (processa as bancadas)
        #    Na 2ª iteração retorna True (aciona o break do loop)
        respostas_wait = [False, True]
        monkeypatch.setattr(
            stop_event, 
            "wait", 
            lambda timeout: respostas_wait.pop(0) if respostas_wait else True
        )

        # 3. Executa a função
        loop_processamento_periodico()

        # 4. Asserts
        assert mock_processar_db.call_count == 2
        mock_processar_db.assert_has_calls(
            [
                call(1, janela_horaria="1h", horas=3600),
                call(2, janela_horaria="1h", horas=3600),
            ],
            any_order=True,
        )

        # Garante que as bancadas ativas foram limpas do set após o processamento
        assert len(bancadas_ativas) == 0
    
    @patch(f"{NOME_DO_MODULO}.processar_sensor_db")
    def test_processamento_erro_recoloca_bancada_nas_ativas(self, mock_processar_db, monkeypatch):
        """Se o processamento de uma bancada falhar, ela deve ser devolvida ao conjunto de bancadas ativas."""
        from hydrotwin.communication.events import bancadas_ativas, stop_event

        bancadas_ativas.add(1)
        mock_processar_db.side_effect = Exception("Falha ao calcular médias")

        monkeypatch.setattr(stop_event, "wait", lambda timeout: True)

        loop_processamento_periodico()

        assert 1 in bancadas_ativas


# ==============================================================================
# TESTES: TRANSPORT READER
# ==============================================================================

class TestTransportReader:

    def test_reader_recebe_telemetria_com_sucesso(self, monkeypatch):
        """Módulo lê linha do transporte, realiza o parse e adiciona à fila de dados."""
        from hydrotwin.communication.events import fila_dados, stop_event

        mock_transport = MagicMock()
        mock_transport.receber.side_effect = [
            "B1,7.0,1.2,25.0,22.0,500.0,80.0,60.0",
            ""  # Para evitar loop infinito antes do stop_event
        ]

        def mock_sleep(_):
            stop_event.set()

        monkeypatch.setattr("time.sleep", mock_sleep)

        transport_reader(mock_transport)

        assert not fila_dados.empty()
        dados = fila_dados.get()
        assert dados[0] == 1  # bancada_id
        mock_transport.fechar.assert_called_once()

    def test_reader_recebe_confirmacao_arduino(self, monkeypatch):
        """Módulo identifica confirmações do Arduino e direciona para a fila de confirmação."""
        from hydrotwin.communication.events import fila_confirmacao, stop_event

        mock_transport = MagicMock()
        mock_transport.receber.return_value = "PARAMS_OK,bancada_id=5"

        def mock_sleep(_):
            stop_event.set()

        monkeypatch.setattr("time.sleep", mock_sleep)

        transport_reader(mock_transport)

        assert not fila_confirmacao.empty()
        confirmacao = fila_confirmacao.get()
        assert confirmacao["bancada_id"] == 5
        assert confirmacao["status"] == "ok"

    def test_reader_reconexao_sucesso(self, monkeypatch):
        """Simula perda de conexão e reconexão bem-sucedida no transporte."""
        from hydrotwin.communication.events import ready_event, stop_event

        mock_transport = MagicMock()
        # Lança exceção na primeira leitura para acionar bloco de reconexão
        mock_transport.receber.side_effect = Exception("Conexão perdida")
        
        def mock_sleep(_):
            pass

        monkeypatch.setattr("time.sleep", mock_sleep)

        # Na tentativa de reconexão, o conectar() funciona
        mock_transport.conectar.return_value = None

        # Faz o stop_event ser acionado dentro da lógica após reconectar
        def mock_conectar():
            stop_event.set()

        mock_transport.conectar.side_effect = mock_conectar

        transport_reader(mock_transport)

        mock_transport.fechar.assert_called()
        mock_transport.conectar.assert_called_once()
        assert ready_event.is_set() is True

    def test_reader_reconexao_falha_5_tentativas_encerra(self, monkeypatch):
        """Se 5 tentativas de reconexão falharem, deve acionar o stop_event."""
        from hydrotwin.communication.events import stop_event

        mock_transport = MagicMock()
        mock_transport.receber.side_effect = Exception("Erro no socket")
        mock_transport.conectar.side_effect = Exception("Falha ao reconectar")

        monkeypatch.setattr("time.sleep", lambda _: None)

        transport_reader(mock_transport)

        assert mock_transport.conectar.call_count == 5
        assert stop_event.is_set() is True


# ==============================================================================
# TESTES: MONITOR DE COMUNICAÇÃO
# ==============================================================================

class TestMonitorComunicacao:

    def test_monitor_detecta_offline_e_restabelecimento(self, monkeypatch):
        """Valida mudança de estado da flag 'comunicacao_offline' conforme o timeout."""
        import hydrotwin.communication.reader as reader_module
        from hydrotwin.communication import events

        # 1. Reseta os estados iniciais
        events.stop_event.clear()
        reader_module.comunicacao_offline = False

        # 2. Define a data base simulada (26 de Julho de 2026)
        agora_simulado = datetime(2026, 7, 26, 14, 0, 0)

        # 3. Cria um Mock para o datetime e faz o .now() retornar a nossa data simulada
        mock_datetime = MagicMock()
        mock_datetime.now.return_value = agora_simulado

        # Substitui a referência do 'datetime' dentro do módulo do reader pelo nosso mock
        monkeypatch.setattr(f"{NOME_DO_MODULO}.datetime", mock_datetime)

        # 4. Configura o 'ultimo_recebimento' inicial como estourado (OFFLINE)
        with events.ultimo_recebimento_lock:
            events.ultimo_recebimento = agora_simulado - timedelta(
                seconds=TIMEOUT_COMUNICACAO + 100
            )

        execucoes = 0

        def mock_wait(timeout):
            nonlocal execucoes
            execucoes += 1

            if execucoes == 1:
                # 1ª iteração: O monitor já avaliou e deve ter ligado a flag de offline
                assert reader_module.comunicacao_offline is True

                # Simula que um novo dado acabou de chegar (restabelecimento)
                with events.ultimo_recebimento_lock:
                    events.ultimo_recebimento = agora_simulado

                # Retorna False para continuar o loop para a 2ª iteração
                return False

            else:
                # 2ª iteração: O monitor detectou a volta dos dados e desligou o offline
                assert reader_module.comunicacao_offline is False

                # Retorna True para acionar o 'break' e fechar o monitor
                return True

        monkeypatch.setattr(events.stop_event, "wait", mock_wait)

        # 5. Executa a função
        monitor_comunicacao()

        # Asserts
        assert execucoes == 2