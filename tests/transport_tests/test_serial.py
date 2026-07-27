from unittest.mock import MagicMock
import pytest
import serial

# Substitua 'seu_modulo' pelo caminho do arquivo onde a classe está definida
from hydrotwin.transport import SerialTransport


# ==============================================================================
# FIXTURES E MOCKS
# ==============================================================================

@pytest.fixture
def mock_serial(monkeypatch):
    """
    Mocka o construtor do PySerial e a função time.sleep 
    para rodar os testes sem dependência de hardware e instantaneamente.
    """
    mock_serial_obj = MagicMock()
    mock_serial_obj.is_open = True

    mock_serial_ctor = MagicMock(return_value=mock_serial_obj)
    
    monkeypatch.setattr("serial.Serial", mock_serial_ctor)
    monkeypatch.setattr("time.sleep", MagicMock())

    return mock_serial_ctor, mock_serial_obj


# ==============================================================================
# TESTES UNITÁRIOS
# ==============================================================================

class TestSerialTransport:

    # ----------------------------------------------------------------------
    # CONEXÃO
    # ----------------------------------------------------------------------

    def test_conectar_sucesso(self, mock_serial):
        """Valida a inicialização correta e a limpeza do buffer de entrada."""
        mock_ctor, mock_obj = mock_serial

        transport = SerialTransport(porta="COM3", baud_rate=115200)
        transport.conectar()

        mock_ctor.assert_called_once_with("COM3", 115200, timeout=0.5)
        mock_obj.reset_input_buffer.assert_called_once()
        assert transport.serial == mock_obj

    def test_conectar_falha_serial_exception(self, monkeypatch):
        """Valida se o erro serial.SerialException é capturado e relançado como ConnectionError."""
        mock_ctor = MagicMock(side_effect=serial.SerialException("Porta ocupada"))
        monkeypatch.setattr("serial.Serial", mock_ctor)

        transport = SerialTransport(porta="COM3")

        with pytest.raises(ConnectionError, match="Falha ao conectar serial em COM3: Porta ocupada"):
            transport.conectar()

        assert transport.serial is None

    # ----------------------------------------------------------------------
    # ENVIO
    # ----------------------------------------------------------------------

    def test_enviar_sucesso_adiciona_quebra_de_linha(self, mock_serial):
        """Garante que a mensagem é codificada em UTF-8 e acrescida de '\\n' se necessário."""
        _, mock_obj = mock_serial
        transport = SerialTransport("COM3")
        transport.conectar()

        transport.enviar("PING")

        mock_obj.write.assert_called_once_with(b"PING\n")
        mock_obj.flush.assert_called_once()

    def test_enviar_sucesso_com_quebra_de_linha_existente(self, mock_serial):
        """Garante que não duplica a quebra de linha caso a mensagem já contenha '\\n'."""
        _, mock_obj = mock_serial
        transport = SerialTransport("COM3")
        transport.conectar()

        transport.enviar("PING\n")

        mock_obj.write.assert_called_once_with(b"PING\n")

    def test_enviar_desconectado_lanca_runtime_error(self):
        """Tentar enviar com serial desconectada deve lançar RuntimeError."""
        transport = SerialTransport("COM3")

        with pytest.raises(RuntimeError, match="Serial desconectada"):
            transport.enviar("TESTE")

    def test_enviar_serial_fechada_lanca_runtime_error(self, mock_serial):
        """Tentar enviar quando is_open for False deve lançar RuntimeError."""
        _, mock_obj = mock_serial
        mock_obj.is_open = False

        transport = SerialTransport("COM3")
        transport.conectar()

        with pytest.raises(RuntimeError, match="Serial desconectada"):
            transport.enviar("TESTE")

    # ----------------------------------------------------------------------
    # RECEBIMENTO
    # ----------------------------------------------------------------------

    def test_receber_sucesso(self, mock_serial):
        """Valida a leitura e decodificação correta da string sem espaços nas pontas."""
        _, mock_obj = mock_serial
        mock_obj.readline.return_value = b"OK\r\n"

        transport = SerialTransport("COM3")
        transport.conectar()

        resposta = transport.receber()

        assert resposta == "OK"
        mock_obj.readline.assert_called_once()

    def test_receber_dados_vazios_retorna_none(self, mock_serial):
        """Quando a leitura do buffer não traz dados, deve retornar None."""
        _, mock_obj = mock_serial
        mock_obj.readline.return_value = b""

        transport = SerialTransport("COM3")
        transport.conectar()

        assert transport.receber() is None

    def test_receber_caracteres_invalidos_substitui_sem_quebrar(self, mock_serial):
        """Valida se o parâmetro errors='replace' lida com bytes UTF-8 corrompidos."""
        _, mock_obj = mock_serial
        # O byte b'\xff' é inválido em UTF-8 puro
        mock_obj.readline.return_value = b"DADO_\xff_OK\n"

        transport = SerialTransport("COM3")
        transport.conectar()

        resposta = transport.receber()
        assert "DADO_" in resposta
        assert "_OK" in resposta

    def test_receber_desconectado_lanca_runtime_error(self):
        """Tentar receber sem conectar deve lançar RuntimeError."""
        transport = SerialTransport("COM3")

        with pytest.raises(RuntimeError, match="Serial desconectada"):
            transport.receber()

    # ----------------------------------------------------------------------
    # FECHAMENTO E CONTEXT MANAGER
    # ----------------------------------------------------------------------

    def test_fechar_conexao_aberta(self, mock_serial):
        """Fecha a porta serial e reseta a referência interna."""
        _, mock_obj = mock_serial
        transport = SerialTransport("COM3")
        transport.conectar()

        transport.fechar()

        mock_obj.close.assert_called_once()
        assert transport.serial is None

    def test_fechar_sem_conexao_nao_gera_erro(self):
        """Garante resiliência ao chamar fechar() sem conexão ativa."""
        transport = SerialTransport("COM3")
        transport.fechar()
        assert transport.serial is None

    def test_context_manager(self, mock_serial):
        """Valida se as chamadas de __enter__ e __exit__ conectam e fecham o recurso automaticamente."""
        mock_ctor, mock_obj = mock_serial

        with SerialTransport("COM3") as transport:
            assert transport.serial == mock_obj
            mock_ctor.assert_called_once()

        mock_obj.close.assert_called_once()
        assert transport.serial is None