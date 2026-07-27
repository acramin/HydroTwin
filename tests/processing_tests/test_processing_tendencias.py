import pandas as pd
import pytest

# Substitua 'seu_modulo' pelo nome do seu arquivo Python
from hydrotwin.processing import (
    JANELA_ANALISE,
    LIMIAR_VARIACAO,
    calcular_variacao,
    classificar_tendencia,
    gerar_mensagem,
    analisar_tendencias,
)


# ==============================================================================
# FIXTURES E MOCKS
# ==============================================================================

@pytest.fixture(autouse=True)
def mock_metricas_config(monkeypatch):
    """
    Isola o dicionário METRICAS_CONFIG usando monkeypatch.
    Evita dependência de configurações externas da aplicação.
    """
    dummy_config = {
        "ph": {"label": "pH", "unidade": ""},
        "temperatura_agua": {"label": "Temperatura da Água", "unidade": "°C"},
        "ec": {"label": "Eletrocondutividade", "unidade": "uS/cm"},
        "nivel_tanque": {"label": "Nível do Tanque", "unidade": "%"},
    }
    monkeypatch.setattr("hydrotwin.processing.METRICAS_CONFIG", dummy_config)


# ==============================================================================
# TESTES DAS FUNÇÕES AUXILIARES
# ==============================================================================

class TestFuncoesAuxiliares:

    def test_calcular_variacao_sucesso(self):
        """Testa cálculo de variação entre média recente e antiga."""
        # Aumento de 100 para 110 (+10%)
        assert calcular_variacao(100.0, 110.0) == pytest.approx(0.10)
        # Queda de 100 para 90 (-10%)
        assert calcular_variacao(100.0, 90.0) == pytest.approx(-0.10)

    def test_calcular_variacao_media_antiga_zero_ou_none(self):
        """Garante que médias antigas nulas ou próximas de zero retornam 0.0 sem ZeroDivisionError."""
        assert calcular_variacao(0.0, 10.0) == 0.0
        assert calcular_variacao(1e-7, 10.0) == 0.0
        assert calcular_variacao(None, 10.0) == 0.0

    @pytest.mark.parametrize(
        "variacao, tendencia_esperada",
        [
            (0.02, "Estável"),           # Abaixo de 5%
            (-0.049, "Estável"),         # Próximo do limiar inferior
            (0.05, "Subindo"),           # Exatamente no limiar positivo
            (0.15, "Subindo"),           # Entre 5% e 20%
            (-0.10, "Descendo"),         # Negativo entre -5% e -20%
            (0.20, "Mudança Brusca"),    # Exatamente no limiar de mudança brusca
            (-0.35, "Mudança Brusca"),   # Queda forte (>= 20% em valor absoluto)
        ],
    )
    def test_classificar_tendencia(self, variacao, tendencia_esperada):
        """Testa os enquadramentos da variação nas classificações correspondentes."""
        assert classificar_tendencia(variacao) == tendencia_esperada

    def test_gerar_mensagem_formatacao(self):
        """Garante que as mensagens são formatadas adequadamente para cada tendência."""
        msg_estavel = gerar_mensagem("pH", "Estável", 2.5, "")
        assert "permanece estável com variação de 2.5%" in msg_estavel

        msg_subindo = gerar_mensagem("Temperatura da Água", "Subindo", 12.3, "°C")
        assert "apresenta tendência de subindo (12.3%)" in msg_subindo

        msg_brusca = gerar_mensagem("Eletrocondutividade", "Mudança Brusca", -25.0, "uS/cm")
        assert "apresentou mudança brusca de -25.0%" in msg_brusca


# ==============================================================================
# TESTES DA FUNÇÃO PRINCIPAL: analisar_tendencias
# ==============================================================================

class TestAnalisarTendencias:

    def test_dataframe_none_ou_vazio(self):
        """Valida o retorno quando o DataFrame é None ou vazio."""
        res_none = analisar_tendencias(None)
        assert res_none["status"] == "Sem dados"
        assert res_none["score"] == 0
        assert res_none["total_tendencias"] == 0
        assert res_none["tendencias"] == []

        res_vazio = analisar_tendencias(pd.DataFrame())
        assert res_vazio["status"] == "Sem dados"

    def test_dados_insuficientes_para_duas_janelas(self):
        """
        Garante que séries com menos dados do que 2x a janela são ignoradas,
        pois é necessário comparar o período antigo com o recente.
        """
        janela = 5  # Precisa de pelo menos 10 registros
        df = pd.DataFrame({"ph": [7.0] * 9})

        resultado = analisar_tendencias(df, janela=janela)
        assert resultado["status"] == "Estável"
        assert resultado["total_tendencias"] == 0

    def test_ignora_nivel_tanque(self):
        """Garante que 'nivel_tanque' é ignorado mesmo se houver variação alta."""
        janela = 3
        # 3 antigos com 0 e 3 recentes com 100
        df = pd.DataFrame({"nivel_tanque": [0, 0, 0, 100, 100, 100]})

        resultado = analisar_tendencias(df, janela=janela)
        assert resultado["status"] == "Estável"
        assert resultado["total_tendencias"] == 0

    def test_cenario_estavel(self):
        """Valida que variações inferiores a 5% são consideradas estáveis e não entram no retorno."""
        janela = 3
        # Média antiga = 100.0, Média recente = 103.0 (Variação de +3%)
        df = pd.DataFrame({"ph": [100.0, 100.0, 100.0, 103.0, 103.0, 103.0]})

        resultado = analisar_tendencias(df, janela=janela)
        assert resultado["status"] == "Estável"
        assert resultado["score"] == 0
        assert resultado["total_tendencias"] == 0
        assert resultado["tendencias"] == []

    def test_tendencia_subindo_e_descendo(self):
        """Valida detecção de tendência 'Subindo' e 'Descendo' gerando status 'Atenção'."""
        janela = 3
        # Média antiga = 100.0, Média recente = 110.0 (+10% -> Subindo, Score 50)
        df = pd.DataFrame({"ph": [100.0, 100.0, 100.0, 110.0, 110.0, 110.0]})

        resultado = analisar_tendencias(df, janela=janela)

        assert resultado["status"] == "Atenção"
        assert resultado["score"] == 50
        assert resultado["total_tendencias"] == 1

        tendencia = resultado["tendencias"][0]
        assert tendencia["sensor"] == "ph"
        assert tendencia["status"] == "Subindo"
        assert tendencia["score"] == 50
        assert tendencia["variacao_percentual"] == 10.0

    def test_tendencia_mudanca_brusca(self):
        """Valida variação superior a 20% gerando status 'Mudança Brusca' e score geral 'Crítico'."""
        janela = 3
        # Média antiga = 10.0, Média recente = 13.0 (+30% -> Mudança Brusca, Score 100)
        df = pd.DataFrame({"temperatura_agua": [10.0, 10.0, 10.0, 13.0, 13.0, 13.0]})

        resultado = analisar_tendencias(df, janela=janela)

        assert resultado["status"] == "Crítico"
        assert resultado["score"] == 100
        assert resultado["total_tendencias"] == 1

        tendencia = resultado["tendencias"][0]
        assert tendencia["status"] == "Mudança Brusca"
        assert tendencia["score"] == 100
        assert tendencia["variacao_percentual"] == 30.0

    def test_ordenacao_por_variacao_absoluta(self):
        """
        Verifica se os resultados são ordenados pela magnitude da variação percentual
        (em valor absoluto), independentemente de ser positiva ou negativa.
        """
        janela = 3
        # ph: +10% de variação
        # ec: -30% de variação (variação absoluta maior)
        df = pd.DataFrame({
            "ph": [100.0, 100.0, 100.0, 110.0, 110.0, 110.0],
            "ec": [100.0, 100.0, 100.0, 70.0, 70.0, 70.0],
        })

        resultado = analisar_tendencias(df, janela=janela)

        assert resultado["total_tendencias"] == 2
        # 'ec' deve vir primeiro por ter variação absoluta maior (|-30%| > |10%|)
        assert resultado["tendencias"][0]["sensor"] == "ec"
        assert resultado["tendencias"][0]["variacao_percentual"] == -30.0

        assert resultado["tendencias"][1]["sensor"] == "ph"
        assert resultado["tendencias"][1]["variacao_percentual"] == 10.0

    def test_tratamento_de_dados_com_nulos(self):
        """Valida que valores nulos ou inválidos são limpos antes da divisão de janelas."""
        janela = 3
        # 6 valores válidos necessários (3 antigos e 3 recentes) + 2 incorretos/nulos
        dados = ["invalido", None, 10.0, 10.0, 10.0, 15.0, 15.0, 15.0]
        df = pd.DataFrame({"ph": dados})

        resultado = analisar_tendencias(df, janela=janela)

        # Média antiga: 10.0, Média recente: 15.0 -> Variação +50% (Mudança Brusca)
        assert resultado["status"] == "Crítico"
        assert resultado["total_tendencias"] == 1
        assert resultado["tendencias"][0]["variacao_percentual"] == 50.0