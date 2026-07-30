from __future__ import annotations

import streamlit as st

# Configuração da Página
st.set_page_config(page_title="Central de Ajuda - HydroTwin", layout="wide", page_icon="❓")

# ==========================================
# ❓ CABEÇALHO DA PÁGINA
# ==========================================
st.title("❓ Central de Ajuda & FAQ")
st.caption("Guia rápido de uso, interpretação de status e respostas para as principais dúvidas do HydroTwin.")

# Resumo do Projeto em Container
with st.container(border=True):
    st.markdown(
        """
        O **HydroTwin** centraliza o cadastro, o acompanhamento e a leitura operacional de bancadas hidropônicas.
        A plataforma organiza os dados coletados pelos sensores, calcula indicadores consolidados e destaca **alertas, anomalias e tendências** para facilitar a tomada de decisão rápida no campo.
        """
    )

    # Indicadores Rápidos da Plataforma
    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("Páginas do Sistema", "4", help="Visão Geral, Detalhado, Painel e Ajuda")
    with m2:
        st.metric("Níveis de Status", "3", help="Saudável, Atenção e Crítico")
    with m3:
        st.metric("Profundidade de Leitura", "Resumo + Detalhado")

st.divider()

# ==========================================
# 📊 GUIA DE INTERPRETAÇÃO DE STATUS
# ==========================================
st.subheader("🟢🟡🔴 Como Interpretar os Status do Sistema")
st.markdown("O sistema analisa os dados brutos e consolida o estado de cada bancada com base nos limites operacionais:")

col_s1, col_s2, col_s3 = st.columns(3)

with col_s1:
    st.success("**🟢 Saudável**")
    st.caption("Todos os indicadores (pH, EC, temperatura, nível) estão dentro da faixa ideal esperada para a cultura.")

with col_s2:
    st.warning("**🟡 Atenção**")
    st.caption("Um ou mais sensores começaram a se aproximar dos limites críticos. Exige acompanhamento preventivo.")

with col_s3:
    st.error("**🔴 Crítico**")
    st.caption("Condição fora do padrão ou alto risco operacional detectado. Requer intervenção técnica imediata.")

st.info(
    "💡 **Status Consolidado:** Na página de monitoramento detalhado, o status combina **risco atual, anomalia e tendência**. "
    "Isso evita ambiguidades quando um indicador parece normal, mas a tendência aponta para um problema futuro."
)

st.divider()

# ==========================================
# 📚 PERGUNTAS FREQUENTES (ORGANIZADAS EM ABAS)
# ==========================================
st.subheader("📖 Perguntas Frequentes & Funcionalidades")

tab_passos, tab_geral, tab_detalhado, tab_simulacao = st.tabs([
    "🚀 Primeiros Passos",
    "📊 Visão Geral",
    "🔍 Monitoramento Detalhado",
    "⚙️ Permissões & Simulação"
])

# --- TAB 1: PRIMEIROS PASSOS ---
with tab_passos:
    st.markdown("### 🚀 Começando com o HydroTwin")
    
    with st.expander("O que o sistema faz de forma geral?"):
        st.markdown(
            """
            - **Cadastra bancadas e culturas:** Vincula cada área de cultivo à sua planta correspondente.
            - **Recebe leituras dos sensores:** Armazena histórico bruto de pH, EC, temperatura, umidade e nível.
            - **Processamento automático:** Calcula *scores*, detecta tendências e identifica anomalias.
            - **Geração de alertas:** Notifica quando algum parâmetro sai da zona segura.
            """
        )

    with st.expander("Como cadastrar uma nova bancada?"):
        st.markdown(
            """
            1. Acesse o **Painel de Controle** no menu lateral.
            2. Abra a aba **➕ Nova Bancada**.
            3. Informe o **Nome da Bancada**, selecione a **Cultura Inicial** e defina a **Data de Plantio**.
            4. Clique em **💾 Cadastrar Bancada**.
            
            *(Nota: Apenas usuários com perfil **Admin** podem cadastrar novas bancadas).*
            """
        )

# --- TAB 2: VISÃO GERAL ---
with tab_geral:
    st.markdown("### 📊 Entendendo a Visão Geral")

    with st.expander("O que vejo na página Visão Geral?"):
        st.markdown(
            """
            A página **Visão Geral** foi desenhada para leitura rápida em *dashboards* de acompanhamento:
            * **Status das Bancadas:** Resumo de cor e estado atual de todas as bancadas ativas.
            * **Indicadores Gerais (KPIs):** Valores consolidados mais recentes de pH, EC, Temperatura, Umidade e Nível do Tanque.
            * **Alertas Ativos:** Lista centralizada de problemas que exigem atenção imediata.
            """
        )

    with st.expander("Como interpretar os KPIs da Visão Geral?"):
        st.markdown(
            """
            * **pH e EC:** Indicam se a solução nutritiva está balanceada para a cultura ativa.
            * **Nível do Tanque:** Exibe **OK** para nível adequado e **Baixo** quando necessita reabastecimento.
            * **Temperatura e Umidade:** Auxiliam na gestão do microclima e circulação da solução.
            """
        )

    with st.expander("Por que aparece 'Sem Dados' ou 'Nenhum KPI'?"):
        st.write(
            "Isso ocorre quando a bancada foi cadastrada recentemente e os sensores físicos "
            "(ou o simulador) ainda não enviaram leituras suficientes para os cálculos estatísticos."
        )

# --- TAB 3: MONITORAMENTO DETALHADO ---
with tab_detalhado:
    st.markdown("### 🔍 Análise Aprofundada & Gráficos")

    with st.expander("O que muda na página Monitoramento Detalhado?"):
        st.markdown(
            """
            Esta página foca em **uma bancada por vez** e traz diagnósticos avançados:
            * **Score de Risco:** Nível de severidade calculado a partir da janela de leituras.
            * **Contribuição do Risco:** Mostra exatamente qual variável (ex: pH) está pesando mais para o alerta.
            * **Anomalias:** Destaque visual de medições estatisticamente fora do padrão histórico.
            * **Tendência Operacional:** Indica se a condição da bancada está *Melhorando*, *Estável* ou *Piorando*.
            """
        )

    with st.expander("Como usar os modos de visualização dos gráficos (Zona vs. Linha)?"):
        st.markdown(
            """
            * **Modo Zona:** Exibe faixas coloridas indicando os limites ideais, de atenção e críticos de cada parâmetro.
            * **Modo Linha:** Foca na evolução temporal contínua da métrica para facilitar a visualização de tendências.
            """
        )

# --- TAB 4: PERMISSÕES & SIMULAÇÃO ---
with tab_simulacao:
    st.markdown("### ⚙️ Perfis de Acesso e Testes")

    with st.expander("Quais são os perfis de acesso (Roles)?"):
        st.markdown(
            """
            * **`admin` (Administrador):** Possui permissão total para cadastrar bancadas, adicionar filetes e alterar configurações.
            * **`viewer` (Visualizador):** Perfil padrão de novos cadastros. Pode visualizar dashboards, gráficos e alertas, mas não realiza alterações.
            """
        )

    with st.expander("Para que serve a Simulação?"):
        st.write(
            "A simulação gera telemetria sintética (dados falsos de sensores) em intervalos curtos. "
            "Ela serve para testar e demonstrar todas as funcionalidades de alertas, gráficos e "
            "processamento do HydroTwin mesmo sem sensores físicos conectados no momento."
        )

st.divider()

# ==========================================
# 🔗 RODAPÉ & REPOSITÓRIO
# ==========================================
st.markdown("### ❓ Dúvidas não encontradas?")
st.info(
    "📖 Para consultar a documentação técnica completa, código fonte e arquitetura do projeto, "
    "acesse o repositório oficial no GitHub: **[HydroTwin GitHub Repository](https://github.com/acramin/HydroTwin)**"
)