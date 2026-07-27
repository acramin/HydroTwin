import threading
from unittest.mock import MagicMock, patch
import pytest

# Substitua 'hydrotwin.runner' pelo caminho real do arquivo
NOME_DO_MODULO = "hydrotwin.communication.manager"

from hydrotwin.communication.manager import (
    conexao_worker,
    encerrar_sistema,
    main,
    ready_event,
    stop_event,
    worker_com_barreira,
)


# ==============================================================================
# FIXTURES DE ISOLAMENTO DE ESTADO
# ==============================================================================

@pytest.fixture(autouse=True)
def reset_global_events():
    """
    Garante que os eventos globais 'stop_event' e 'ready_event' 
    estejam limpos antes e depois de cada teste para não haver contaminação cruzada.
    """
    stop_event.clear()
    ready_event.clear()
    yield
    stop_event.clear()
    ready_event.clear()


@pytest.fixture
def mock_transport():
    """Cria um mock para os objetos de transporte (Serial / TCP)."""
    transport = MagicMock()
    return transport


# ==============================================================================
# TESTES: conexao_worker
# ==============================================================================

class TestConexaoWorker:

    def test_conexao_worker_sucesso(self, mock_transport):
        """Quando a conexão é bem-sucedida, deve sinalizar o ready_event."""
        conexao_worker(mock_transport)

        mock_transport.conectar.assert_called_once()
        assert ready_event.is_set() is True
        assert stop_event.is_set() is False

    def test_conexao_worker_falha(self, mock_transport):
        """Quando ocorre erro na conexão, deve sinalizar o stop_event."""
        mock_transport.conectar.side_effect = Exception("Falha física de cabo")

        conexao_worker(mock_transport)

        mock_transport.conectar.assert_called_once()
        assert ready_event.is_set() is False
        assert stop_event.is_set() is True


# ==============================================================================
# TESTES: worker_com_barreira
# ==============================================================================

class TestWorkerComBarreira:

    def test_worker_com_barreira_executa_apos_ready(self):
        """Sinaliza ready_event e verifica se a função alvo é executada com os argumentos."""
        mock_target = MagicMock()
        ready_event.set()  # Simula barreira liberada

        worker_com_barreira(mock_target, "arg1", 123)

        mock_target.assert_called_once_with("arg1", 123)

    def test_worker_com_barreira_interrompe_se_stop_event_setado(self):
        """Se stop_event estiver ativo, o worker deve encerrar sem chamar a função alvo."""
        mock_target = MagicMock()
        stop_event.set()

        worker_com_barreira(mock_target, "arg1")

        mock_target.assert_not_called()


# ==============================================================================
# TESTES: encerrar_sistema
# ==============================================================================

class TestEncerrarSistema:

    def test_encerrar_sistema_sucesso(self, mock_transport):
        """Valida se o stop_event é setado, o transporte é fechado e as threads sofrem join."""
        mock_thread_1 = MagicMock(spec=threading.Thread)
        mock_thread_1.is_alive.return_value = True

        mock_thread_2 = MagicMock(spec=threading.Thread)
        mock_thread_2.is_alive.return_value = False

        threads = [mock_thread_1, mock_thread_2]

        encerrar_sistema(mock_transport, threads)

        assert stop_event.is_set() is True
        mock_transport.fechar.assert_called_once()
        mock_thread_1.join.assert_called_once_with(timeout=1.0)
        mock_thread_2.join.assert_not_called()

    def test_encerrar_sistema_trata_excecao_no_fechamento_do_transporte(self, mock_transport):
        """Garante resiliência caso transport.fechar() lance uma exceção."""
        mock_transport.fechar.side_effect = Exception("Erro ao fechar socket")
        threads = []

        # Não deve interromper a execução do fluxo de encerramento
        encerrar_sistema(mock_transport, threads)

        assert stop_event.is_set() is True
        mock_transport.fechar.assert_called_once()


# ==============================================================================
# TESTES: main
# ==============================================================================

class TestMain:

    @patch(f"{NOME_DO_MODULO}.get_transport_mode")
    @patch(f"{NOME_DO_MODULO}.SerialTransport")
    @patch(f"{NOME_DO_MODULO}.TCPServerTransport")
    @patch(f"{NOME_DO_MODULO}.threading.Thread")
    @patch(f"{NOME_DO_MODULO}.encerrar_sistema")
    def test_main_modo_serial(
        self,
        mock_encerrar,
        mock_thread_class,
        mock_tcp_cls,
        mock_serial_cls,
        mock_get_mode,
        monkeypatch,
    ):
        """Valida se a main instancia SerialTransport quando o modo retornado for 'serial'."""
        mock_get_mode.return_value = "serial"
        mock_thread_instance = MagicMock()
        mock_thread_class.return_value = mock_thread_instance

        # Faz o loop da main() sair na primeira iteração
        def mock_sleep(_):
            stop_event.set()

        monkeypatch.setattr("time.sleep", mock_sleep)

        main()

        mock_serial_cls.assert_called_once_with('/dev/ttyACM0', 9600)
        mock_tcp_cls.assert_not_called()
        assert mock_thread_instance.start.call_count == 6
        mock_encerrar.assert_called_once()

    @patch(f"{NOME_DO_MODULO}.get_transport_mode")
    @patch(f"{NOME_DO_MODULO}.SerialTransport")
    @patch(f"{NOME_DO_MODULO}.TCPServerTransport")
    @patch(f"{NOME_DO_MODULO}.threading.Thread")
    @patch(f"{NOME_DO_MODULO}.encerrar_sistema")
    def test_main_modo_tcp(
        self,
        mock_encerrar,
        mock_thread_class,
        mock_tcp_cls,
        mock_serial_cls,
        mock_get_mode,
        monkeypatch,
    ):
        """Valida se a main instancia TCPServerTransport quando o modo for diferente de 'serial'."""
        mock_get_mode.return_value = "tcp"
        mock_thread_instance = MagicMock()
        mock_thread_class.return_value = mock_thread_instance

        def mock_sleep(_):
            stop_event.set()

        monkeypatch.setattr("time.sleep", mock_sleep)

        main()

        mock_tcp_cls.assert_called_once_with('0.0.0.0', 65432)
        mock_serial_cls.assert_not_called()
        mock_encerrar.assert_called_once()

    @patch(f"{NOME_DO_MODULO}.get_transport_mode")
    @patch(f"{NOME_DO_MODULO}.SerialTransport")
    @patch(f"{NOME_DO_MODULO}.threading.Thread")
    @patch(f"{NOME_DO_MODULO}.encerrar_sistema")
    def test_main_captura_keyboard_interrupt(
        self,
        mock_encerrar,
        mock_thread_class,
        mock_serial_cls,
        mock_get_mode,
        monkeypatch,
    ):
        """Garante que a interrupção por KeyboardInterrupt (Ctrl+C) aciona o encerramento gracioso."""
        mock_get_mode.return_value = "serial"

        # Simula a interrupção do usuário ao entrar no time.sleep
        monkeypatch.setattr("time.sleep", MagicMock(side_effect=KeyboardInterrupt))

        main()

        mock_encerrar.assert_called_once()