from datetime import datetime
from queue import Empty, Full
from unittest.mock import MagicMock, call, patch
import pytest

# Altere 'hydrotwin.sender' para o caminho real do seu arquivo
NOME_DO_MODULO = "hydrotwin.communication.sender"

from hydrotwin.communication.sender import (
    atualizar_status,
    enfileirar_envio,
    enviar_parametros_ideais_worker,
    formatar_mensagem_parametros,
    limpar_status_envio,
    obter_parametros_cultura,
    obter_status_envio,
)


# ==============================================================================
# FIXTURES E RESET DE ESTADO GLOBAL
# ==============================================================================

@pytest.fixture(autouse=True)
def reset_global_state():
    """
    Limpa e reinicializa os eventos, filas e dicionários globais
    antes e depois de cada teste para garantir isolamento.
    """
    from hydrotwin.communication import events

    events.stop_event.clear()
    events.ready_event.set()  # Por padrão, deixa o ready_event ativo nos testes

    # Esvazia filas
    while not events.fila_envio.empty():
        try:
            events.fila_envio.get_nowait()
        except Empty:
            break

    while not events.fila_confirmacao.empty():
        try:
            events.fila_confirmacao.get_nowait()
        except Empty:
            break

    with events.status_envios_lock:
        events.status_envios.clear()

    yield

    events.stop_event.clear()
    events.ready_event.clear()

    with events.status_envios_lock:
        events.status_envios.clear()


@pytest.fixture
def mock_transport():
    """Retorna um mock para o objeto de transporte."""
    transport = MagicMock()
    return transport


# ==============================================================================
# TESTES: FORMATADOR DE MENSAGEM
# ==============================================================================

class TestFormatarMensagemParametros:

    def test_formatar_mensagem_parametros_sucesso(self):
        """Garante a formatação adequada da string enviada ao hardware."""
        params = {
            "ph_min": 5.5,
            "ph_max": 6.5,
            "ec_min": 1.2,
            "ec_max": 1.8,
            "dias_ciclo": 30,
        }
        resultado = formatar_mensagem_parametros(
            bancada_id=1, cultura_id=2, parametros=params
        )

        esperado = "PARAMS,bancada_id=1,cultura_id=2,ph_min=5.5,ph_max=6.5,ec_min=1.2,ec_max=1.8,dias_ciclo=30\n"
        assert resultado == esperado

    def test_formatar_mensagem_parametros_vazio(self):
        """Retorna None se o dicionário de parâmetros for None ou vazio."""
        assert formatar_mensagem_parametros(1, 1, None) is None
        assert formatar_mensagem_parametros(1, 1, {}) is None


# ==============================================================================
# TESTES: INTERFACE FRONTEND E ESTADO DE ENVIO
# ==============================================================================

class TestInterfaceEnvio:

    def test_enfileirar_envio_sucesso(self):
        """Valida se a solicitação é enfileirada corretamente."""
        from hydrotwin.communication.events import fila_envio

        sucesso = enfileirar_envio(bancada_id=1, cultura_id=10)

        assert sucesso is True
        assert not fila_envio.empty()
        assert fila_envio.get() == (1, 10)

    @patch("hydrotwin.communication.events.fila_envio.put")
    def test_enfileirar_envio_fila_cheia(self, mock_put):
        """Retorna False se a fila de envio estiver cheia."""
        mock_put.side_effect = Full()

        sucesso = enfileirar_envio(bancada_id=1, cultura_id=10)

        assert sucesso is False

    def test_obter_e_limpar_status_envio(self):
        """Testa gravação, consulta e remoção do status de envio."""
        atualizar_status(1, "sucesso", "Parâmetros configurados.")

        # Consulta status existente
        status = obter_status_envio(1)
        assert status["status"] == "sucesso"
        assert status["mensagem"] == "Parâmetros configurados."

        # Limpa status
        limpar_status_envio(1)

        # Consulta status inexistente
        status_limpo = obter_status_envio(1)
        assert status_limpo["status"] == "nao_iniciado"


# ==============================================================================
# TESTES: WORKER DE ENVIO (enviar_parametros_ideais_worker)
# ==============================================================================

class TestEnviarParametrosIdeaisWorker:

    @patch(f"{NOME_DO_MODULO}.obter_parametros_cultura")
    def test_worker_fluxo_sucesso_completo(self, mock_obter_params, mock_transport):
        """Simula fluxo completo: lê fila, busca params, envia e recebe confirmação OK."""
        from hydrotwin.communication.events import (
            fila_confirmacao,
            fila_envio,
            ready_event,
            stop_event,
        )

        # 1. Garante o estado inicial limpo dos eventos do módulo
        ready_event.set()
        stop_event.clear()

        # 2. Mock dos parâmetros retornados do banco de dados
        mock_obter_params.return_value = {
            "ph_min": 5.5,
            "ph_max": 6.5,
            "ec_min": 1.2,
            "ec_max": 1.8,
            "dias_ciclo": 30,
        }

        # 3. Prepara os dados das filas de envio e de confirmação
        bancada_id = 1
        cultura_id = 10
        fila_envio.put((bancada_id, cultura_id))
        fila_confirmacao.put({"status": "ok", "bancada_id": bancada_id, "motivo": None})

        # 4. Controla o encerramento do worker sem interromper o processamento atual
        get_original = fila_envio.get

        def mock_get_envio(*args, **kwargs):
            # Quando a fila estiver vazia (na 2ª iteração do worker), sinaliza o fim
            if fila_envio.empty():
                stop_event.set()
                raise Empty
            return get_original(*args, **kwargs)

        fila_envio.get = mock_get_envio

        # 5. Executa a função do worker
        try:
            enviar_parametros_ideais_worker(mock_transport)
        finally:
            # Restaura o método original para não afetar outros testes
            fila_envio.get = get_original

        # --- ASSERTS ---

        # Verifica se o transporte realizou o envio exatamente uma vez
        mock_transport.enviar.assert_called_once()

        # Garante que a confirmação foi consumida no loop de confirmação
        assert fila_confirmacao.empty(), "A fila de confirmação deveria ter sido consumida pelo worker."

        # Verifica se o status final no banco/cache é de 'sucesso'
        status = obter_status_envio(bancada_id)
        assert status["status"] == "sucesso"
        assert "sucesso" in status["mensagem"].lower()

    @patch(f"{NOME_DO_MODULO}.obter_parametros_cultura")
    def test_worker_cultura_nao_encontrada(self, mock_obter_params, mock_transport, monkeypatch):
        """Quando a cultura não existe no banco, atualiza status para 'erro'."""
        from hydrotwin.communication.events import fila_envio, stop_event

        mock_obter_params.return_value = None
        fila_envio.put((1, 99))

        def mock_get(timeout=None):
            stop_event.set()
            raise Empty()

        # Altera o get na segunda iteração para interromper
        original_get = fila_envio.get

        def side_effect_get(*args, **kwargs):
            item = original_get(*args, **kwargs)
            stop_event.set()
            return item

        monkeypatch.setattr(fila_envio, "get", side_effect_get)

        enviar_parametros_ideais_worker(mock_transport)

        status = obter_status_envio(1)
        assert status["status"] == "erro"
        assert "não encontrada" in status["mensagem"]
        mock_transport.enviar.assert_not_called()

    @patch(f"{NOME_DO_MODULO}.obter_parametros_cultura")
    def test_worker_rejeicao_pelo_hardware(self, mock_obter_params, mock_transport):
        """Trata a resposta 'PARAMS_ERROR' enviada pelo Arduino."""
        from hydrotwin.communication.events import (
            fila_confirmacao,
            fila_envio,
            stop_event,
        )

        mock_obter_params.return_value = {"ph_min": 5.5, "ph_max": 6.5, "ec_min": 1.2, "ec_max": 1.8, "dias_ciclo": 30}

        fila_envio.put((1, 10))
        fila_confirmacao.put({
            "status": "erro",
            "bancada_id": 1,
            "motivo": "Sensor descalibrado"
        })

        get_original = fila_envio.get

        def mock_get_envio(*args, **kwargs):
            # Quando a fila estiver vazia (na 2ª iteração do worker), sinaliza o fim
            if fila_envio.empty():
                stop_event.set()
                raise Empty
            return get_original(*args, **kwargs)

        fila_envio.get = mock_get_envio

        try:
            enviar_parametros_ideais_worker(mock_transport)
        finally:
            # Restaura o método original para não afetar outros testes
            fila_envio.get = get_original

        assert fila_confirmacao.empty(), "A fila de confirmação deveria ter sido consumida pelo worker."

        status = obter_status_envio(1)
        assert status["status"] == "erro"
        assert "Sensor descalibrado" in status["mensagem"]

    @patch(f"{NOME_DO_MODULO}.CONFIRM_TIMEOUT", 0.1)
    @patch(f"{NOME_DO_MODULO}.obter_parametros_cultura")
    def test_worker_timeout_confirmacao(self, mock_obter_params, mock_transport):
        """Marca o envio com erro após estourar o limite de tempo sem resposta do hardware."""
        from hydrotwin.communication.events import fila_envio, stop_event

        mock_obter_params.return_value = {"ph_min": 5.5, "ph_max": 6.5, "ec_min": 1.2, "ec_max": 1.8, "dias_ciclo": 30}

        fila_envio.put((1, 10))
        # Nenhuma resposta colocada na fila_confirmacao

        get_original = fila_envio.get
        
        def mock_get_envio(*args, **kwargs):
            # Quando a fila estiver vazia (na 2ª iteração do worker), sinaliza o fim
            if fila_envio.empty():
                stop_event.set()
                raise Empty
            return get_original(*args, **kwargs)

        fila_envio.get = mock_get_envio

        try:
            enviar_parametros_ideais_worker(mock_transport)
        finally:
            # Restaura o método original para não afetar outros testes
            fila_envio.get = get_original

        status = obter_status_envio(1)
        assert status["status"] == "erro"
        assert "Timeout" in status["mensagem"]

    @patch(f"{NOME_DO_MODULO}.obter_parametros_cultura")
    def test_worker_gerencia_confirmacoes_fora_de_ordem(self, mock_obter_params, mock_transport):
        """Garante que respostas de outras bancadas fiquem salvas em cache local sem serem descartadas."""
        from hydrotwin.communication.events import (
            fila_confirmacao,
            fila_envio,
            stop_event,
        )

        mock_obter_params.return_value = {"ph_min": 5.5, "ph_max": 6.5, "ec_min": 1.2, "ec_max": 1.8, "dias_ciclo": 30}

        # Solicitação para Bancada 1
        fila_envio.put((1, 10))

        # Fila de confirmação entrega primeiro a resposta da Bancada 2, e depois a da Bancada 1
        fila_confirmacao.put({"status": "ok", "bancada_id": 2, "motivo": None})
        fila_confirmacao.put({"status": "ok", "bancada_id": 1, "motivo": None})

        get_original = fila_envio.get
        
        def mock_get_envio(*args, **kwargs):
            if fila_envio.empty():
                stop_event.set()
                raise Empty
            return get_original(*args, **kwargs)

        fila_envio.get = mock_get_envio

        try:
            enviar_parametros_ideais_worker(mock_transport)
        finally:
            fila_envio.get = get_original

        assert fila_confirmacao.empty(), "A fila de confirmação deveria ter sido consumida pelo worker."

        # Status da Bancada 1 deve ser concluído com sucesso
        status_b1 = obter_status_envio(1)
        assert status_b1["status"] == "sucesso"