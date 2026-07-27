from datetime import datetime, timedelta
from unittest.mock import MagicMock
import pytest

# Substitua 'seu_modulo' pelo nome do seu arquivo Python
from hydrotwin import obter_status_comunicacao


# ==============================================================================
# FIXTURES E MOCKS
# ==============================================================================

@pytest.fixture
def mock_conn():
    """
    Simula o objeto de conexão do banco de dados (conn) e o cursor.
    """
    conn = MagicMock()
    cursor = MagicMock()
    conn.cursor.return_value = cursor
    return conn, cursor


# ==============================================================================
# TESTES DA FUNÇÃO: obter_status_comunicacao
# ==============================================================================

class TestObterStatusComunicacao:

    def test_sem_dados(self, mock_conn):
        """Garante retorno 'SEM DADOS' e None quando o banco retorna None (tabela vazia)."""
        conn, cursor = mock_conn
        cursor.fetchone.return_value = (None,)

        status, data = obter_status_comunicacao(conn)

        assert status == "SEM DADOS"
        assert data is None
        cursor.execute.assert_called_once()

    def test_status_online(self, mock_conn, monkeypatch):
        """Retorna 'ONLINE' quando a última leitura ocorreu a menos de 1200s (ex: 5 minutos atrás)."""
        conn, cursor = mock_conn

        agora = datetime(2026, 7, 26, 12, 0, 0)
        cinco_min_atras = agora - timedelta(minutes=5)

        cursor.fetchone.return_value = (cinco_min_atras.isoformat(),)

        # Mock para fixar o datetime.now()
        class DummyDatetime(datetime):
            @classmethod
            def now(cls, tz=None):
                return agora

        monkeypatch.setattr("hydrotwin.db.crud.datetime", DummyDatetime)

        status, data = obter_status_comunicacao(conn)

        assert status == "ONLINE"
        assert data == cinco_min_atras

    def test_status_offline(self, mock_conn, monkeypatch):
            """Retorna 'OFFLINE' quando a última leitura ocorreu há mais de 1200s (ex: 30 minutos atrás)."""
            conn, cursor = mock_conn

            agora = datetime(2026, 7, 26, 12, 0, 0)
            trinta_min_atras = agora - timedelta(minutes=30)  # 1800 segundos

            cursor.fetchone.return_value = (trinta_min_atras.isoformat(),)

            # Mockando o método now diretamente no datetime importado pelo módulo alvo
            class MockDatetime:
                @classmethod
                def now(cls, tz=None):
                    return agora
                
                # Mantém a compatibilidade com o fromisoformat que a função usa
                @classmethod
                def fromisoformat(cls, date_string):
                    return datetime.fromisoformat(date_string)

            monkeypatch.setattr("hydrotwin.db.crud.datetime", MockDatetime)

            status, data = obter_status_comunicacao(conn)

            assert status == "OFFLINE"
            assert data == trinta_min_atras

    def test_limiar_exato_1200_segundos(self, mock_conn, monkeypatch):
        """
        Valida a regra de fronteira em exatamente 1200 segundos (20 minutos).
        Como a condição é `segundos > 1200`, no limite exato de 1200 ainda deve retornar 'ONLINE'.
        """
        conn, cursor = mock_conn

        agora = datetime(2026, 7, 26, 12, 0, 0)
        exatos_20_min_atras = agora - timedelta(seconds=1200)

        cursor.fetchone.return_value = (exatos_20_min_atras.isoformat(),)

        class DummyDatetime(datetime):
            @classmethod
            def now(cls, tz=None):
                return agora

        monkeypatch.setattr("hydrotwin.db.crud.datetime", DummyDatetime)

        status, data = obter_status_comunicacao(conn)

        assert status == "ONLINE"
        assert data == exatos_20_min_atras