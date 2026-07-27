import pandas as pd
import pytest

# Substitua 'seu_modulo' pelo caminho do arquivo onde está a sua função
from hydrotwin.processing import (
    JANELA_ANALISE,
    calcular_desvio_percentual, # precisa tirar o _ do nome na declaração no módulo
    classificar_desvio, # precisa tirar o _ do nome na declaração no módulo
    detectar_anomalias,
)


# ==============================================================================
# FIXTURES E MOCKS
# ==============================================================================

@pytest.fixture(autouse=True)
def mock_metricas_config(monkeypatch):
    """
    Isola o dicionário METRICAS_CONFIG usando monkeypatch do pytest.
    Evita dependência da configuração externa do 'hydrotwin.helpers'.
    """
    dummy_config = {
        "ph": {"label": "pH", "unidade": ""},
        "temperatura_agua": {"label": "Temperatura da Água", "unidade": "°C"},
        "nivel_tanque": {"label": "Nível do Tanque", "unidade": "%"},
    }
    # Substitui METRICAS_CONFIG no módulo em teste
    monkeypatch.setattr("hydrotwin.processing.METRICAS_CONFIG", dummy_config)


# ==============================================================================
# TESTES DAS FUNÇÕES AUXILIARES
# ==============================================================================

class TestFuncoesAuxiliares:

    def test_calcular_desvio_percentual_sucesso(self):
        """Testa o cálculo matemático de desvio relativo para valores válidos."""
        # Valor 110 em relação à média 100 representa 10% (0.10)
        assert calcular_desvio_percentual(110.0, 100.0) == pytest.approx(0.10)
        assert calcular_desvio_percentual(90.0, 100.0) == pytest.approx(0.10)

    def test_calcular_desvio_percentual_media_zero_ou_none(self):
        """Garante que médias nulas ou próximas de zero retornam 0.0 sem estourar ZeroDivisionError."""
        assert calcular_desvio_percentual(10.0, 0.0) == 0.0
        assert calcular_desvio_percentual(10.0, 1e-7) == 0.0
        assert calcular_desvio_percentual(10.0, None) == 0.0

    @pytest.mark.parametrize(
        "desvio, status_esperado",
        [
            (0.05, "Saudável"),
            (0.10, "Saudável"),  # Limiar exato do Saudável
            (0.11, "Atenção"),
            (0.20, "Atenção"),   # Limiar exato do Atenção
            (0.21, "Crítico"),
        ],
    )
    def test_classificar_desvio(self, desvio, status_esperado):
        """Testa o enquadramento nos limiares previstos."""
        assert classificar_desvio(desvio) == status_esperado


# ==============================================================================
# TESTES DA FUNÇÃO PRINCIPAL: detectar_anomalias
# ==============================================================================

class TestDetectarAnomalias:

    def test_dataframe_none_ou_vazio(self):
        """Valida o retorno padronizado quando o DataFrame é None ou vazio."""
        res_none = detectar_anomalias(None)
        assert res_none["status"] == "Sem dados"
        assert res_none["score"] == 0
        assert res_none["total_anomalias"] == 0
        assert res_none["anomalias"] == []

        res_vazio = detectar_anomalias(pd.DataFrame())
        assert res_vazio["status"] == "Sem dados"

    def test_dados_insuficientes_para_janela(self):
        """Ignora séries com quantidade de registros válidos menor que a janela informada."""
        janela = 10
        # Apenas 9 registros no DataFrame (a janela pede 10)
        df = pd.DataFrame({"ph": [7.0] * 9})

        resultado = detectar_anomalias(df, janela=janela)
        assert resultado["status"] == "Saudável"
        assert resultado["total_anomalias"] == 0

    def test_ignora_coluna_nivel_tanque(self):
        """Garante que 'nivel_tanque' é pulado, mesmo contendo desvios bruscos."""
        janela = 5
        df = pd.DataFrame({"nivel_tanque": [0.0, 0.0, 0.0, 0.0, 100.0]})

        resultado = detectar_anomalias(df, janela=janela)
        assert resultado["status"] == "Saudável"
        assert resultado["total_anomalias"] == 0

    def test_cenario_saudavel(self):
        """Valida o comportamento quando todas as métricas estão dentro do desvio tolerável (<= 10%)."""
        janela = 5
        # Média recente = 10.0, Valor atual = 10.5 (Desvio de 5%)
        df = pd.DataFrame({"ph": [10.0, 10.0, 10.0, 10.0, 10.5]})

        resultado = detectar_anomalias(df, janela=janela)
        assert resultado["status"] == "Saudável"
        assert resultado["score"] == 0
        assert resultado["total_anomalias"] == 0
        assert resultado["anomalias"] == []

    def test_detecta_anomalia_atencao(self):
        """Garante que um desvio entre 10% e 20% gera o status 'Atenção'."""
        janela = 5
        # Média recente (4 primeiros) = 10.0, Valor atual = 11.5 (Desvio de 15%)
        df = pd.DataFrame({"ph": [10.0, 10.0, 10.0, 10.0, 11.5]})

        resultado = detectar_anomalias(df, janela=janela)

        assert resultado["status"] == "Atenção"
        assert resultado["score"] == 50
        assert resultado["total_anomalias"] == 1

        anomalia = resultado["anomalias"][0]
        assert anomalia["sensor"] == "ph"
        assert anomalia["status"] == "Atenção"
        assert anomalia["score"] == 50
        assert anomalia["desvio_percentual"] == 15.0

    def test_detecta_anomalia_critica(self):
        """Garante que um desvio maior que 20% gera o status 'Crítico'."""
        janela = 5
        # Média recente = 10.0, Valor atual = 15.0 (Desvio de 50%)
        df = pd.DataFrame({"temperatura_agua": [10.0, 10.0, 10.0, 10.0, 15.0]})

        resultado = detectar_anomalias(df, janela=janela)

        assert resultado["status"] == "Crítico"
        assert resultado["score"] == 100
        assert resultado["total_anomalias"] == 1

        anomalia = resultado["anomalias"][0]
        assert anomalia["sensor"] == "temperatura_agua"
        assert anomalia["status"] == "Crítico"
        assert anomalia["score"] == 100
        assert anomalia["desvio_percentual"] == 50.0

    def test_ordenacao_e_status_geral_com_multiplas_anomalias(self):
        """
        Garante que:
        1. O status e score geral refletem a anomalia mais grave.
        2. A lista de anomalias é ordenada do maior score para o menor.
        """
        janela = 5
        # ph -> Atenção (+15%)
        # temperatura_agua -> Crítico (+50%)
        df = pd.DataFrame({
            "ph": [10.0, 10.0, 10.0, 10.0, 11.5],
            "temperatura_agua": [10.0, 10.0, 10.0, 10.0, 15.0],
        })

        resultado = detectar_anomalias(df, janela=janela)

        assert resultado["status"] == "Crítico"
        assert resultado["score"] == 100
        assert resultado["total_anomalias"] == 2

        # Primeiro item deve ser o mais crítico
        assert resultado["anomalias"][0]["sensor"] == "temperatura_agua"
        assert resultado["anomalias"][0]["score"] == 100

        # Segundo item deve ser a atenção
        assert resultado["anomalias"][1]["sensor"] == "ph"
        assert resultado["anomalias"][1]["score"] == 50

    def test_tratamento_de_valores_invalidos_ou_nulos(self):
        """Verifica se valores não numéricos são ignorados na conversão mantendo a execução correta."""
        janela = 5
        # Valores inválidos serão convertidos para NaN e descartados pelo .dropna()
        dados = ["texto_invalido", None, 10.0, 10.0, 10.0, 10.0, 15.0]
        df = pd.DataFrame({"ph": dados})

        resultado = detectar_anomalias(df, janela=janela)

        assert resultado["status"] == "Crítico"
        assert resultado["total_anomalias"] == 1