import socket
from unittest.mock import MagicMock
import pytest

# Substitua 'seu_modulo' pelo arquivo/módulo real onde as classes estão declaradas
from hydrotwin.transport import TCPClientTransport, TCPServerTransport

# Nome do módulo para redirecionar as chamadas do monkeypatch
NOME_DO_MODULO = "hydrotwin.transport.tcp_transport"


# ==============================================================================
# FIXTURES DE SOCKET MOCK
# ==============================================================================

@pytest.fixture
def mock_socket_setup(monkeypatch):
    """
    Mocka a fábrica de sockets (socket.socket) criando objetos simulados
    para a socket principal e para a socket de conexão aceita (cliente).
    """
    mock_main_socket = MagicMock()
    mock_conn_socket = MagicMock()

    # Simula o aceite de conexão retornando um novo socket e um endereço fictício
    mock_main_socket.accept.return_value = (mock_conn_socket, ("127.0.0.1", 54321))

    # Construtor do socket.socket retornará a socket principal por padrão
    mock_socket_class = MagicMock(return_value=mock_main_socket)
    monkeypatch.setattr(f"{NOME_DO_MODULO}.socket.socket", mock_socket_class)

    return {
        "class": mock_socket_class,
        "main_socket": mock_main_socket,
        "conn_socket": mock_conn_socket,
    }


# ==============================================================================
# TESTES: TCPServerTransport
# ==============================================================================

class TestTCPServerTransport:

    def test_conectar_sucesso(self, mock_socket_setup):
        """Valida se o servidor configura SO_REUSEADDR, faz bind, listen e aguarda accept()."""
        mocks = mock_socket_setup
        server = TCPServerTransport(host="127.0.0.1", port=5000)

        server.conectar()

        mocks["main_socket"].setsockopt.assert_called_once_with(
            socket.SOL_SOCKET, socket.SO_REUSEADDR, 1
        )
        mocks["main_socket"].bind.assert_called_once_with(("127.0.0.1", 5000))
        mocks["main_socket"].listen.assert_called_once_with(1)
        mocks["main_socket"].accept.assert_called_once()
        mocks["conn_socket"].settimeout.assert_called_once_with(0.5)

        assert server.servidor == mocks["main_socket"]
        assert server.conn == mocks["conn_socket"]

    def test_conectar_falha_lanca_connection_error(self, mock_socket_setup):
        """Em caso de falha de conexão ou bind, deve chamar fechar() e lançar ConnectionError."""
        mocks = mock_socket_setup
        mocks["main_socket"].bind.side_effect = OSError("Porta em uso")

        server = TCPServerTransport(host="127.0.0.1", port=5000)

        with pytest.raises(ConnectionError, match="Falha na conexão do Servidor TCP"):
            server.conectar()

        assert server.servidor is None
        assert server.conn is None

    def test_enviar_sucesso(self, mock_socket_setup):
        """Valida se a mensagem é enviada via sendall, adicionando '\\n' se necessário."""
        mocks = mock_socket_setup
        server = TCPServerTransport()
        server.conectar()

        server.enviar("MENSAGEM")

        mocks["conn_socket"].sendall.assert_called_once_with(b"MENSAGEM\n")

    def test_enviar_com_quebra_de_linha_existente(self, mock_socket_setup):
        """Garante que a mensagem não receba um '\\n' duplicado se já contiver ao final."""
        mocks = mock_socket_setup
        server = TCPServerTransport()
        server.conectar()

        server.enviar("MENSAGEM\n")

        mocks["conn_socket"].sendall.assert_called_once_with(b"MENSAGEM\n")

    def test_enviar_sem_cliente_lanca_runtime_error(self):
        """Tentativa de envio sem um cliente conectado dispara RuntimeError."""
        server = TCPServerTransport()

        with pytest.raises(RuntimeError, match="Nenhum cliente conectado"):
            server.enviar("DADO")

    def test_receber_linha_completa_via_recv(self, mock_socket_setup):
        """Valida o recebimento de dados e extração de uma linha encerrada em '\\n'."""
        mocks = mock_socket_setup
        mocks["conn_socket"].recv.return_value = b"DADO_RECEBIDO\n"

        server = TCPServerTransport()
        server.conectar()

        mensagem = server.receber()

        assert mensagem == "DADO_RECEBIDO"
        assert server.buffer == ""

    def test_receber_com_dados_ja_presentes_no_buffer(self, mock_socket_setup):
        """Se o buffer já possuir uma linha completa, deve retornar sem acionar o socket.recv."""
        mocks = mock_socket_setup
        server = TCPServerTransport()
        server.conectar()

        server.buffer = "LINHA1\nLINHA2"

        # Primeira chamada consome LINHA1 direto do buffer
        msg1 = server.receber()
        assert msg1 == "LINHA1"
        assert server.buffer == "LINHA2"

        mocks["conn_socket"].recv.assert_not_called()

    def test_receber_dados_incompletos_retorna_none(self, mock_socket_setup):
        """Retorna None caso os dados lidos do socket ainda não contenham quebra de linha."""
        mocks = mock_socket_setup
        mocks["conn_socket"].recv.return_value = b"DADO_INCOMPLETO"

        server = TCPServerTransport()
        server.conectar()

        mensagem = server.receber()

        assert mensagem is None
        assert server.buffer == "DADO_INCOMPLETO"

    def test_receber_timeout_retorna_none(self, mock_socket_setup):
        """Exceção de socket.timeout durante a leitura deve ser tratada retornando None."""
        mocks = mock_socket_setup
        mocks["conn_socket"].recv.side_effect = socket.timeout()

        server = TCPServerTransport()
        server.conectar()

        mensagem = server.receber()

        assert mensagem is None

    def test_receber_conexao_encerrada_pelo_cliente(self, mock_socket_setup):
        """Retorno de bytes vazios indica desconexão do cliente e deve retornar None."""
        mocks = mock_socket_setup
        mocks["conn_socket"].recv.return_value = b""

        server = TCPServerTransport()
        server.conectar()

        mensagem = server.receber()

        assert mensagem is None

    def test_receber_sem_cliente_lanca_runtime_error(self):
        """Chamar receber sem ter um cliente conectado deve disparar RuntimeError."""
        server = TCPServerTransport()

        with pytest.raises(RuntimeError, match="Nenhum cliente conectado"):
            server.receber()

    def test_fechar_sucesso(self, mock_socket_setup):
        """Garante encerramento gracioso via shutdown e close dos sockets do cliente e do servidor."""
        mocks = mock_socket_setup
        server = TCPServerTransport()
        server.conectar()

        server.fechar()

        mocks["conn_socket"].shutdown.assert_called_once_with(socket.SHUT_RDWR)
        mocks["conn_socket"].close.assert_called_once()
        mocks["main_socket"].close.assert_called_once()

        assert server.conn is None
        assert server.servidor is None


# ==============================================================================
# TESTES: TCPClientTransport
# ==============================================================================

class TestTCPClientTransport:

    def test_conectar_sucesso(self, mock_socket_setup):
        """Valida a conexão do cliente TCP com alteração dinâmica de timeout."""
        mocks = mock_socket_setup
        client = TCPClientTransport(host="127.0.0.1", port=5000)

        client.conectar()

        mocks["main_socket"].connect.assert_called_once_with(("127.0.0.1", 5000))
        # Verifica se alterou o timeout para 3.0 para conexão e depois para 0.5 para leituras
        mocks["main_socket"].settimeout.assert_any_call(3.0)
        mocks["main_socket"].settimeout.assert_any_call(0.5)

        assert client.socket == mocks["main_socket"]

    def test_conectar_falha_lanca_connection_error(self, mock_socket_setup):
        """Garante que falhas de conexão limpem o socket e lancem ConnectionError."""
        mocks = mock_socket_setup
        mocks["main_socket"].connect.side_effect = ConnectionRefusedError("Conexão recusada")

        client = TCPClientTransport(host="127.0.0.1", port=5000)

        with pytest.raises(ConnectionError, match="Falha ao conectar cliente TCP"):
            client.conectar()

        assert client.socket is None

    def test_enviar_sucesso(self, mock_socket_setup):
        """Garante envio correto com tratamento do caractere de quebra de linha."""
        mocks = mock_socket_setup
        client = TCPClientTransport()
        client.conectar()

        client.enviar("COMANDO")

        mocks["main_socket"].sendall.assert_called_once_with(b"COMANDO\n")

    def test_enviar_desconectado_lanca_runtime_error(self):
        """Tentar enviar com o cliente desconectado deve disparar RuntimeError."""
        client = TCPClientTransport()

        with pytest.raises(RuntimeError, match="Cliente TCP desconectado"):
            client.enviar("TESTE")

    def test_receber_sucesso(self, mock_socket_setup):
        """Leitura de linha completa vinda do servidor."""
        mocks = mock_socket_setup
        mocks["main_socket"].recv.return_value = b"RESPOSTA_SERVIDOR\n"

        client = TCPClientTransport()
        client.conectar()

        resposta = client.receber()

        assert resposta == "RESPOSTA_SERVIDOR"

    def test_receber_timeout(self, mock_socket_setup):
        """Timeout no recv do cliente deve ser capturado e retornar None."""
        mocks = mock_socket_setup
        mocks["main_socket"].recv.side_effect = socket.timeout()

        client = TCPClientTransport()
        client.conectar()

        assert client.receber() is None

    def test_receber_desconectado_lanca_runtime_error(self):
        """Chamar receber com cliente desconectado deve disparar RuntimeError."""
        client = TCPClientTransport()

        with pytest.raises(RuntimeError, match="Cliente TCP desconectado"):
            client.receber()

    def test_fechar_sucesso(self, mock_socket_setup):
        """Valida execução do shutdown e close ao encerrar o cliente."""
        mocks = mock_socket_setup
        client = TCPClientTransport()
        client.conectar()

        client.fechar()

        mocks["main_socket"].shutdown.assert_called_once_with(socket.SHUT_RDWR)
        mocks["main_socket"].close.assert_called_once()
        assert client.socket is None