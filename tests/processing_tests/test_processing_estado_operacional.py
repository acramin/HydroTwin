import pytest

# Substitua 'seu_modulo' pelo nome do seu arquivo Python
from hydrotwin.processing import (
    LIMITES_OPERACIONAIS,
    STATUS_SCORE,
    avaliar_faixa,
    construir_config_limites,
    mensagem_sensor,
    avaliar_estado_operacional,
)


# ==============================================================================
# FIXTURES E MOCKS
# ==============================================================================

@pytest.fixture(autouse=True)
def mock_helpers(monkeypatch):
    """
    Isola dependências externas do módulo 'hydrotwin.helpers':
    - METRICAS_CONFIG para labels e unidades.
    - to_float para conversão segura de tipos.
    """
    dummy_config = {
        "ph": {"label": "pH", "unidade": ""},
        "ec": {"label": "Condutividade Elétrica", "unidade": "mS/cm"},
        "temperatura_agua": {"label": "Temperatura da Água", "unidade": "°C"},
    }

    def dummy_to_float(val):
        if val is None:
            return None
        try:
            return float(val)
        except (ValueError, TypeError):
            return None

    monkeypatch.setattr("hydrotwin.processing.METRICAS_CONFIG", dummy_config)
    monkeypatch.setattr("hydrotwin.helpers.to_float", dummy_to_float)


# ==============================================================================
# TESTES DAS FUNÇÕES AUXILIARES
# ==============================================================================

class TestFuncoesAuxiliares:

    @pytest.mark.parametrize(
        "valor, faixa_ideal, faixa_atencao, status_esperado",
        [
            # Faixa ideal: (5.5, 6.5) | Faixa atenção: (5.0, 7.0)
            (6.0, (5.5, 6.5), (5.0, 7.0), "Saudável"),
            (5.5, (5.5, 6.5), (5.0, 7.0), "Saudável"),  # Limite inferior ideal
            (6.5, (5.5, 6.5), (5.0, 7.0), "Saudável"),  # Limite superior ideal
            (5.2, (5.5, 6.5), (5.0, 7.0), "Atenção"),   # Dentro da faixa de atenção
            (6.8, (5.5, 6.5), (5.0, 7.0), "Atenção"),   # Dentro da faixa de atenção
            (5.0, (5.5, 6.5), (5.0, 7.0), "Atenção"),   # Limite inferior atenção
            (7.0, (5.5, 6.5), (5.0, 7.0), "Atenção"),   # Limite superior atenção
            (4.9, (5.5, 6.5), (5.0, 7.0), "Crítico"),   # Fora de todas as faixas
            (7.1, (5.5, 6.5), (5.0, 7.0), "Crítico"),   # Fora de todas as faixas
        ],
    )
    def test_avaliar_faixa(self, valor, faixa_ideal, faixa_atencao, status_esperado):
        """Valida se a classificação de faixa atende aos limites exatos estabelecidos."""
        assert avaliar_faixa(valor, faixa_ideal, faixa_atencao) == status_esperado

    def test_mensagem_sensor(self):
        """Garante que as mensagens são formatadas corretamente com base no status do sensor."""
        msg_saudavel = mensagem_sensor("pH", 6.0, "", "Saudável")
        assert msg_saudavel == "pH em faixa ideal (6.00)."

        msg_atencao = mensagem_sensor("pH", 5.2, "", "Atenção")
        assert msg_atencao == "pH fora da faixa ideal (5.20)."

        msg_critico = mensagem_sensor("Condutividade Elétrica", 0.5, "mS/cm", "Crítico")
        assert msg_critico == "Condutividade Elétrica em condição crítica (0.50 mS/cm)."

    def test_construir_config_limites_calculo_delta(self):
        """
        Garante que os limites vindos do banco expandem a faixa ideal em 20%
        para calcular a faixa de atenção.
        """
        limites_db = {
            "ph": (5.0, 7.0),  # Amplitude = 2.0 -> Delta = 0.4
        }
        config = construir_config_limites(limites_db)

        assert "ph" in config
        assert config["ph"]["ideal"] == (5.0, 7.0)
        # Atenção deve ser: min = 5.0 - 0.4 = 4.6 | max = 7.0 + 0.4 = 7.4
        assert config["ph"]["atencao"] == (pytest.approx(4.6), pytest.approx(7.4))
        assert config["ph"]["label"] == "pH"

    def test_construir_config_limites_com_valores_none(self):
        """Valida que valores de limite nulos vindos do banco mantêm o atencao_min/max como None."""
        limites_db = {
            "ph": (None, 7.0),
        }
        config = construir_config_limites(limites_db)
        assert config["ph"]["atencao"] == (None, 7.0)


# ==============================================================================
# TESTES DA FUNÇÃO PRINCIPAL: avaliar_estado_operacional
# ==============================================================================

class TestAvaliarEstadoOperacional:

    def test_dados_vazios_ou_none(self):
        """Retorna 'Sem dados' caso o dicionário de entrada seja None ou vazio."""
        assert avaliar_estado_operacional(None) == {
            "status": "Sem dados",
            "score": 0,
            "sensores": {},
        }
        assert avaliar_estado_operacional({}) == {
            "status": "Sem dados",
            "score": 0,
            "sensores": {},
        }

    def test_dados_sem_sensores_reconhecidos(self):
        """Garante retorno 'Sem dados' se as chaves presentes não baterem com a configuração de limites."""
        dados = {"luminosidade": 500.0}  # Não está no LIMITES_OPERACIONAIS por padrão

        resultado = avaliar_estado_operacional(dados)
        assert resultado["status"] == "Sem dados"
        assert resultado["score"] == 0
        assert resultado["sensores"] == {}

    def test_limites_padrao_cenario_saudavel(self):
        """Métrica dentro da faixa ideal usando os limites padrão (LIMITES_OPERACIONAIS)."""
        dados = {
            "ph": 6.0,  # Faixa ideal ph: (5.5, 6.5)
            "ec": 1.5,  # Faixa ideal ec: (1.2, 2.0)
        }

        resultado = avaliar_estado_operacional(dados)

        assert resultado["status"] == "Saudável"
        assert resultado["score"] == 0
        assert len(resultado["sensores"]) == 2