import streamlit as st

from hydrotwin import (
    get_bancadas,
    get_current_user,
    formatar_data
)

from app.components.monitoramento_detalhado import (
    carregar_monitoramento_bancada,
    montar_df_anomalias,
    montar_df_previsoes,
    render_grafico_linha,
    render_grafico_zona,
    render_legenda_zonas,
    VARIAVEIS_ZONA_FORTES,
)

st.set_page_config(page_title="Hydroponic Monitor", layout="wide", page_icon="🌱")

# =========================
# 🔬 Monitoramento Detalhado
# =========================

st.title("🔬 Monitoramento Detalhado")

usuario = get_current_user()
if usuario is None:
    st.error("❌ Você precisa estar autenticado para acessar esta página.")
    st.stop()

rows = get_bancadas()

if not rows and usuario["role"] == "admin":
    st.info("Cadastre uma bancada para acessar o monitoramento detalhado.")
    st.stop()
    
if not rows and usuario["role"] == "viewer":
    st.info("Aguarde até que admin cadastre uma bancada para acessar o monitoramento detalhado.")
    st.stop()

mapa_bancadas = {nome: bancada_id for bancada_id, nome, *_ in rows}
bancada = st.selectbox("Selecione a bancada", sorted(list(mapa_bancadas.keys())))
bancada_id = mapa_bancadas[bancada]

dados = carregar_monitoramento_bancada(bancada_id=bancada_id, horas=24)
df = dados["df"]
proc = dados["proc"]
limites = dados.get("limites") or {}
resultado_anomalias = dados["resultado_anomalias"]
resultado_tendencia = dados["resultado_tendencia"]
col1, col2, col3 = st.columns(3)
if proc:
    status_consolidado = proc.get("consolidado_status") or proc["status"]
    score_consolidado = proc.get("consolidado_score")
    motivo_consolidado = proc.get("consolidado_motivo") or "Sem motivo consolidado disponível para esta leitura."

    col1.metric(
        "Status consolidado",
        status_consolidado,
        help="Classificação unificada para evitar conflito entre risco, anomalia e tendência."
    )
    col2.metric(
        "Score consolidado",
        f'{(score_consolidado if score_consolidado is not None else proc["score"]):.1f}',
        help=(
            "Score consolidado (0-100): maior severidade observada entre risco atual, anomalia e tendência operacional."
        )
    )
    col3.metric(
        "Score de risco",
        f'{proc["score"]:.1f}',
        help="Score de risco estatístico da janela processada."
    )
    st.caption(f"Motivo do consolidado: {motivo_consolidado}")
    st.caption(f'Janela processada: {proc["janela_horaria"]} | Amostras: {proc["n_amostras"]} | Atualizado em: {formatar_data(proc["dth_calculado"])}')
else:
    col1.metric("Status consolidado", "Sem dados")
    col2.metric("Score consolidado", "-")
    col3.metric("Score de risco", "-")
    st.info("Ainda não há agregação para esta bancada. Assim que a próxima leitura bruta entrar, o cálculo será gerado automaticamente.")
    st.stop()

if df.empty:
    st.warning("Sem leituras brutas recentes para exibir gráficos.")
    st.stop()

# GRÁFICOS DE ZONA (candidatos fortes)
st.subheader("Gráficos por variável", help="Visualize a evolução de cada métrica ao longo do tempo. \n\nModo 'Zona': gráficos com faixas de risco coloridas, baseados nos limites da bancada, para destacar rapidamente quando uma métrica está em zona de atenção ou crítica. \n\nModo 'Linha': gráficos tradicionais de linha, focando na tendência temporal sem sobreposição de zonas.")
modo_visualizacao = st.radio(
    "Modo de visualização",
    options=["Zona", "Linha"],
    horizontal=True,
)

if modo_visualizacao == "Zona":
    render_legenda_zonas()

for idx in range(0, len(VARIAVEIS_ZONA_FORTES), 2):
    col_esq, col_dir = st.columns(2)
    metrica_esq, titulo_esq, unidade_esq = VARIAVEIS_ZONA_FORTES[idx]

    with col_esq:
        if modo_visualizacao == "Zona":
            render_grafico_zona(df, metrica_esq, titulo_esq, limites, unidade=unidade_esq)
        else:
            render_grafico_linha(df, metrica_esq, titulo_esq, unidade=unidade_esq)

    if idx + 1 < len(VARIAVEIS_ZONA_FORTES):
        metrica_dir, titulo_dir, unidade_dir = VARIAVEIS_ZONA_FORTES[idx + 1]
        with col_dir:
            if modo_visualizacao == "Zona":
                render_grafico_zona(df, metrica_dir, titulo_dir, limites, unidade=unidade_dir)
            else:
                render_grafico_linha(df, metrica_dir, titulo_dir, unidade=unidade_dir)

# COMPLEMENTAR (mantido para leitura direta)
col1, col2 = st.columns(2)

col3, col4 = st.columns(2)

if "temperatura_ambiente" in df.columns:
    col1.subheader("Temperatura Ambiente")
    col1.line_chart(df.set_index("dth_recebido")["temperatura_ambiente"])
else:
    col1.subheader("Temperatura Ambiente")
    col1.info("Sem coluna de temperatura ambiente nas leituras recentes.")

if "temperatura_agua" in df.columns:
    col2.subheader("Temperatura da Água")
    col2.line_chart(df.set_index("dth_recebido")["temperatura_agua"])
else:
    col2.subheader("Temperatura da Água")
    col2.info("Sem coluna de temperatura da água nas leituras recentes.")

if "umidade" in df.columns:
    col3.subheader("Umidade")
    col3.line_chart(df.set_index("dth_recebido")["umidade"])
else:
    col3.subheader("Umidade")
    col3.info("Sem coluna de umidade nas leituras recentes.")
    
if "nivel_tanque" in df.columns:
    col4.subheader("Nível de Água")
    # nivel_tanque é categórico (0=abaixo ou 100=normal), exibir como status em vez de gráfico
    nivel_atual = df["nivel_tanque"].iloc[-1] if not df.empty else None
    if nivel_atual == 100:
        col4.success("🟢 Normal")
    elif nivel_atual == 0:
        col4.error("🔴 Abaixo")
    else:
        col4.warning(f"⚠️ Indefinido ({nivel_atual})")
else:
    col4.subheader("Nível de Água")
    col4.info("Sem coluna de nível de tanque nas leituras recentes.")

st.subheader("Detecção de anomalias", help="Identifique comportamentos incomuns nos dados. \n\nAnomalias são pontos de dados que se desviam significativamente do comportamento esperado, indicando possíveis problemas no sistema.")
if not resultado_anomalias:
    st.info("Sem dados suficientes para detectar anomalias.")
else:
    anomalia_status = proc.get("anomalia_status") if proc else resultado_anomalias["status"]
    anomalia_score = proc.get("anomalia_score") if proc else resultado_anomalias["score"]

    col_a, col_b, col_c = st.columns(3)
    col_a.metric(
        "Status de anomalia",
        anomalia_status,
        help="Status derivado do Score de Anomalia. \n\nFaixas: 0-59 = Saudável, 60-84 = Atenção, 85-100 = Crítico."
    )
    col_b.metric(
        "Score de Anomalia",
        f'{(anomalia_score if anomalia_score is not None else resultado_anomalias["score"]):.1f}',
        help=(
            "Score de anomalia (0-100): por sensor, usa a pior entre duas lentes: \n\n"
            "(1) desvio estatístico robusto da série recente (z-score) e "
            "(2) violação direta de limite mínimo/máximo. \n\n"
            "O score geral é a média dos 3 maiores scores de anomalia "
            "(ou o maior score monitorado, se não houver anomalias >= 60). "
        ),
    )
    col_c.metric("Sensores com anomalia", resultado_anomalias["total_anomalias"])

    anomalias_df = montar_df_anomalias(resultado_anomalias)
    if not anomalias_df.empty:
        st.dataframe(
            anomalias_df,
            hide_index=True,
        )
    else:
        st.success("Nenhuma anomalia relevante detectada na janela recente.")

st.subheader("Tendência operacional", help="Qual é a direção do sistema? \n\nAnálise de tendência recente para cada sensor, indicando se a métrica está melhorando, piorando ou estável. A previsão geral é derivada do sensor com a tendência mais relevante, mas também mostramos o número total de sensores que indicam uma tendência clara.")
status_tendencia = proc.get("tendencia_status") if proc else resultado_tendencia["status"]
score_tendencia = proc.get("tendencia_score") if proc else resultado_tendencia["score"]
col_a, col_b, col_c = st.columns(3)
col_a.metric(
    "Status previsto",
    status_tendencia,
    help=(
        "Status derivado da tendência operacional. \n\n"
        "Faixas: 0-33 = Saudável, 34-66 = Atenção, 67-100 = Crítico."
    ),
)
col_b.metric(
    "Tendência geral",
    f'{(score_tendencia if score_tendencia is not None else resultado_tendencia["score"]):.1f}',
    help=(
        "Score de tendência (0-100): mede quão consistente e relevante é a tendência recente. \n\n" 
        "Composição por sensor: Consistência direcional (40%), Força da tendência/slope (30%), "
        "Estabilidade da série suavizada (20%) e quantidade de amostras (10%). \n\n"
        "A tendência geral mostra o maior score entre as tendências observadas. "
    ),
)
col_c.metric("Sensores em tendência", resultado_tendencia["total_previsoes"])

st.caption(resultado_tendencia["resumo"])

previsao_df = montar_df_previsoes(resultado_tendencia)
if not previsao_df.empty:
    st.dataframe(
        previsao_df,
        hide_index=True,
    )
else:
    st.info("Ainda não há tendência operacional clara para as leituras recentes.")

st.subheader("Leituras recentes")
with st.expander("Ver dados brutos"):
    if df.empty:
        st.write("Sem dados para exibir")
    else:
        st.dataframe(df, hide_index=True)