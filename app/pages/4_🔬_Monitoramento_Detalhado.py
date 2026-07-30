from __future__ import annotations

import streamlit as st

from hydrotwin import (
    get_bancadas,
    get_current_user,
    formatar_data,
    logger
)

logger.debug("4_🔬_Monitoramento_Detalhado.py")

from app.components.monitoramento_detalhado import (
    carregar_monitoramento_bancada,
    montar_df_anomalias,
    montar_df_previsoes,
    render_grafico_linha,
    render_grafico_zona,
    render_legenda_zonas,
    VARIAVEIS_ZONA_FORTES,
)

# Configuração da Página
st.set_page_config(page_title="Hydroponic Monitor", layout="wide", page_icon="🌱")

st.title("🔬 Monitoramento Detalhado")

# ==========================================
# 🔐 1. Autenticação e Seleção de Bancada
# ==========================================
usuario = get_current_user()
if usuario is None:
    st.error("❌ Você precisa estar autenticado para acessar esta página.")
    st.stop()

rows = get_bancadas()

if not rows:
    if usuario.get("role") == "admin":
        st.info("Cadastre uma bancada para acessar o monitoramento detalhado.")
    else:
        st.info("Aguarde até que o administrador cadastre uma bancada para acessar o monitoramento detalhado.")
    st.stop()

mapa_bancadas = {nome: bancada_id for bancada_id, nome, *_ in rows}
bancada_selecionada = st.selectbox("Selecione a bancada", sorted(list(mapa_bancadas.keys())))
bancada_id = mapa_bancadas[bancada_selecionada]

# ==========================================
# 📊 2. Carregamento de Dados
# ==========================================
dados = carregar_monitoramento_bancada(bancada_id=bancada_id, horas=24)
df = dados["df"]
proc = dados["proc"]
limites = dados.get("limites") or {}
resultado_anomalias = dados["resultado_anomalias"]
resultado_tendencia = dados["resultado_tendencia"]

# ==========================================
# 📈 3. Status Consolidado
# ==========================================
with st.container(border=True):
    if proc:
        status_consolidado = proc.get("consolidado_status") or proc["status"]
        score_consolidado = proc.get("consolidado_score")
        motivo_consolidado = proc.get("consolidado_motivo") or "Sem motivo consolidado disponível para esta leitura."

        c_status, c_score_cons, c_score_risco = st.columns(3)
        c_status.metric(
            "Status Consolidado",
            status_consolidado,
            help="Classificação unificada para evitar conflito entre risco, anomalia e tendência."
        )
        c_score_cons.metric(
            "Score Consolidado",
            f'{(score_consolidado if score_consolidado is not None else proc["score"]):.1f}',
            help="Score consolidado (0-100): maior severidade observada entre risco atual, anomalia e tendência operacional."
        )
        c_score_risco.metric(
            "Score de Risco",
            f'{proc["score"]:.1f}',
            help="Score de risco estatístico da janela processada."
        )
        st.caption(f"**Motivo:** {motivo_consolidado}")
        st.caption(f' Janela: {proc["janela_horaria"]} | Amostras: {proc["n_amostras"]} | Atualizado em: {formatar_data(proc["dth_calculado"])}')
    else:
        c1, c2, c3 = st.columns(3)
        c1.metric("Status Consolidado", "Sem dados")
        c2.metric("Score Consolidado", "-")
        c3.metric("Score de Risco", "-")
        st.info("Ainda não há agregação para esta bancada. Assim que a próxima leitura bruta entrar, o cálculo será gerado automaticamente.")
        st.stop()

if df.empty:
    st.warning("Sem leituras brutas recentes para exibir gráficos.")
    st.stop()

# ==========================================
# 🗺️ 4. Gráficos de Zona (Métricas Fortes)
# ==========================================
st.subheader(
    "Gráficos por Variável Principal",
    help="Visualize a evolução de pH e EC ao longo do tempo com zonas de atenção configuradas."
)

modo_visualizacao = st.radio(
    "Modo de visualização",
    options=["Zona", "Linha"],
    horizontal=True,
    key="modo_vis_main"
)

if modo_visualizacao == "Zona":
    render_legenda_zonas()

# Renderização em grid de 2 colunas
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

# ==========================================
# 🌡️ 5. Variáveis Complementares
# ==========================================
st.divider()
st.subheader("Métricas de Ambiente e Reservatório")

col_temp_amb, col_temp_agua = st.columns(2)
col_umidade, col_nivel = st.columns(2)

with col_temp_amb:
    if "temperatura_ambiente" in df.columns:
        render_grafico_linha(df, "temperatura_ambiente", "Temperatura Ambiente", unidade="°C")
    else:
        st.info("Sem dados de Temperatura Ambiente.")

with col_temp_agua:
    if "temperatura_agua" in df.columns:
        render_grafico_linha(df, "temperatura_agua", "Temperatura da Água", unidade="°C")
    else:
        st.info("Sem dados de Temperatura da Água.")

with col_umidade:
    if "umidade" in df.columns:
        render_grafico_linha(df, "umidade", "Umidade Relativa", unidade="%")
    else:
        st.info("Sem dados de Umidade.")

with col_nivel:
    st.subheader("Nível de Água (Reservatório)")
    if "nivel_tanque" in df.columns:
        nivel_atual = df["nivel_tanque"].iloc[-1] if not df.empty else None
        
        if nivel_atual == 0:
            st.metric("Status do Reservatório", "🟢 Normal", delta="100% Capacidade")
        elif nivel_atual == 1:
            st.metric("Status do Reservatório", "🔴 Crítico (Abaixo)", delta="- Reposição Necessária", delta_color="inverse")
        else:
            st.metric("Status do Reservatório", f"⚠️ Indefinido ({nivel_atual})")
    else:
        st.info("Sem dados de nível de tanque nas leituras recentes.")

# ==========================================
# 🚨 6. Detecção de Anomalias
# ==========================================
st.divider()
st.subheader("Detecção de Anomalias", help="Identifique comportamentos incomuns ou violações de limites.")

if not resultado_anomalias:
    st.info("Sem dados suficientes para detectar anomalias.")
else:
    anomalia_status = proc.get("anomalia_status") if proc else resultado_anomalias["status"]
    anomalia_score = proc.get("anomalia_score") if proc else resultado_anomalias["score"]

    with st.container(border=True):
        col_a, col_b, col_c = st.columns(3)
        col_a.metric("Status de Anomalia", anomalia_status)
        col_b.metric(
            "Score de Anomalia",
            f'{(anomalia_score if anomalia_score is not None else resultado_anomalias["score"]):.1f}'
        )
        col_c.metric("Sensores Afetados", resultado_anomalias["total_anomalias"])

        anomalias_df = montar_df_anomalias(resultado_anomalias)
        if not anomalias_df.empty:
            # Estilização profissional da tabela
            st.dataframe(
                anomalias_df,
                width='stretch',
                hide_index=True,
                column_config={
                    "nome": st.column_config.TextColumn("Sensor", help="Nome da variável"),
                    "status": st.column_config.TextColumn("Status"),
                    "score": st.column_config.ProgressColumn("Score Severidade", min_value=0, max_value=100, format="%.1f"),
                    "valor_atual": st.column_config.NumberColumn("Valor Atual", format="%.2f"),
                    "media_recente": st.column_config.NumberColumn("Média Recente", format="%.2f"),
                    "desvio_percentual": st.column_config.NumberColumn("Desvio %", format="%.1f%%"),
                    "mensagem": st.column_config.TextColumn("Detalhes / Diagnóstico")
                }
            )
        else:
            st.success("Nenhuma anomalia relevante detectada na janela recente.")

# ==========================================
# 📉 7. Tendência Operacional
# ==========================================
st.divider()
st.subheader("Tendência Operacional", help="Análise de direção recente dos parâmetros do sistema.")

status_tendencia = proc.get("tendencia_status") if proc else resultado_tendencia["status"]
score_tendencia = proc.get("tendencia_score") if proc else resultado_tendencia["score"]

with st.container(border=True):
    col_t1, col_t2, col_t3 = st.columns(3)
    col_t1.metric("Status Previsto", status_tendencia)
    col_t2.metric(
        "Tendência Geral",
        f'{(score_tendencia if score_tendencia is not None else resultado_tendencia["score"]):.1f}'
    )
    col_t3.metric("Sensores em Tendência", resultado_tendencia["total_previsoes"])

    st.caption(f"**Resumo:** {resultado_tendencia['resumo']}")

    previsao_df = montar_df_previsoes(resultado_tendencia)
    if not previsao_df.empty:
        # Estilização profissional da tabela
        st.dataframe(
            previsao_df,
            width='stretch',
            hide_index=True,
            column_config={
                "nome": st.column_config.TextColumn("Sensor"),
                "status": st.column_config.TextColumn("Tendência"),
                "score": st.column_config.ProgressColumn("Score Tendência", min_value=0, max_value=100, format="%.1f"),
                "media_antiga": st.column_config.NumberColumn("Média Anterior", format="%.2f"),
                "media_recente": st.column_config.NumberColumn("Média Recente", format="%.2f"),
                "variacao_percentual": st.column_config.NumberColumn("Variação %", format="%.1f%%"),
            }
        )
    else:
        st.info("Ainda não há tendência operacional clara para as leituras recentes.")

# ==========================================
# 📑 8. Dados Brutos
# ==========================================
st.divider()
with st.expander("🔍 Ver leituras brutas recentes"):
    if df.empty:
        st.write("Sem dados para exibir")
    else:
        st.dataframe(df, width='stretch', hide_index=True)