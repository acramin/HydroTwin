from __future__ import annotations

from datetime import datetime
import os
import time
import pandas as pd
import streamlit as st

# Imports do HydroTwin
from hydrotwin import (
    get_bancadas,
    get_current_user,
    gerar_telemetria_tupla,
    is_development_mode,
    logger
)

logger.debug("6_🕹️_Simulador.py")

# Configuração da página
st.set_page_config(
    page_title="HydroTwin - Painel de Simulação",
    layout="wide",
    page_icon="🕹️",
)

# ==========================================
# 🔒 1. TRAVA DE SEGURANÇA (ENV + ADMIN)
# ==========================================
ENV_ATUAL = "Development" if is_development_mode else "Production"
usuario = get_current_user()

if not is_development_mode():
    st.error("🔒 **Acesso Restrito:** Esta página só está disponível em ambiente de **desenvolvimento**.")
    st.info(f"Ambiente detectado: `{ENV_ATUAL}`")
    st.stop()

if usuario is None or usuario.get("role") != "admin":
    st.error("🚫 **Acesso Negado:** Apenas usuários administradores podem acessar o simulador.")
    st.stop()


# ==========================================
# ⚙️ 2. GERENCIAMENTO DE ESTADO (SESSION STATE)
# ==========================================
if "simulando" not in st.session_state:
    st.session_state.simulando = False

if "ultimo_resultado" not in st.session_state:
    st.session_state.ultimo_resultado = None

# ==========================================
# 🧪 3. INTERFACE DE SIMULAÇÃO
# ==========================================
st.title("🧪 Painel de Simulação de Telemetria")
st.caption("Gere dados sintéticos em tempo real para testar o processamento, alertas e dashboards.")

bancadas = get_bancadas() or []

if not bancadas:
    st.warning("⚠️ Nenhuma bancada encontrada no banco de dados. Cadastre ao menos uma bancada primeiro.")
    st.stop()

opcoes_bancada = {"🌐 TODAS AS BANCADAS": "todas"}
for b in bancadas:
    b_id, b_nome = b[0], b[1]
    opcoes_bancada[f"🌱 Bancada: {b_nome} (ID: {b_id})"] = b_id

col_config, col_exec = st.columns([1, 1])

# --- COLUNA DA ESQUERDA: PARÂMETROS E BOTÕES ---
with col_config:
    with st.container(border=True):
        st.subheader("⚙️ Parâmetros da Simulação")

        selecao = st.selectbox(
            "Alvo da Simulação",
            options=list(opcoes_bancada.keys()),
            disabled=st.session_state.simulando,
        )
        target_id = opcoes_bancada[selecao]

        qtd_leituras = st.number_input(
            "Número de Ciclos / Leituras",
            min_value=1,
            max_value=500,
            value=10,
            step=1,
            disabled=st.session_state.simulando,
        )

        intervalo = st.slider(
            "Intervalo entre Leituras (segundos)",
            min_value=0.2,
            max_value=5.0,
            value=1.0,
            step=0.1,
            disabled=st.session_state.simulando,
        )

        injetar_anomalia = st.checkbox(
            "⚠️ Injetar Anomalias Propositais",
            value=False,
            disabled=st.session_state.simulando,
        )

        st.divider()

        col_btn1, col_btn2 = st.columns(2)

        with col_btn1:
            btn_iniciar = st.button(
                "🚀 Iniciar",
                type="primary",
                width='stretch',
                disabled=st.session_state.simulando,
            )

        with col_btn2:
            btn_cancelar = st.button(
                "🛑 Cancelar",
                type="secondary",
                width='stretch',
                disabled=not st.session_state.simulando,
            )

        # Trata clique em Iniciar
        if btn_iniciar:
            st.session_state.simulando = True
            st.session_state.ultimo_resultado = None
            st.rerun()

        # Trata clique em Cancelar
        if btn_cancelar:
            st.session_state.simulando = False
            st.toast("🛑 Simulação interrompida pelo usuário!", icon="⚠️")
            st.rerun()

# --- COLUNA DA DIREITA: EXECUÇÃO E VISUALIZAÇÃO ---
with col_exec:
    with st.container(border=True):
        st.subheader("📊 Visualização em Tempo Real")

        # Estado 1: Parado (sem executar nada no momento)
        if not st.session_state.simulando:
            # Se acabou de concluir uma simulação, mostra o resumo final
            if st.session_state.ultimo_resultado:
                res = st.session_state.ultimo_resultado
                if res["status"] == "sucesso":
                    st.success(f"✅ Última simulação concluída com sucesso! Total de {res['total']} leituras geradas.")
                else:
                    st.warning("🛑 A última simulação foi cancelada antes de terminar.")

                if res["historico"]:
                    st.caption("📈 Histórico final da última execução:")
                    df_final = pd.DataFrame(res["historico"]).set_index("Horário")
                    st.line_chart(df_final[["pH", "EC"]], height=220)
            else:
                st.info("Configure os parâmetros ao lado e clique em **Iniciar**.")

        # Estado 2: Executando a simulação em tempo real
        else:
            col_m1, col_m2, col_m3 = st.columns(3)
            metric_ph = col_m1.empty()
            metric_ec = col_m2.empty()
            metric_temp = col_m3.empty()

            chart_placeholder = st.empty()
            status_box = st.status("🚀 Processando simulação...", expanded=True)
            barra_progresso = st.progress(0)

            historico_tempo_real = []
            total_processado = 0
            cancelado = False

            for i in range(1, qtd_leituras + 1):
                # Se o usuário clicou em cancelar no meio do loop
                if not st.session_state.simulando:
                    cancelado = True
                    break

                ids_para_rodar = [b[0] for b in bancadas] if target_id == "todas" else [target_id]

                for b_id in ids_para_rodar:
                    dados_tupla = gerar_telemetria_tupla(bancada_id=b_id, com_anomalia=injetar_anomalia)
                    
                    # Descomente se quiser persistir no banco de dados:
                    # inserir_leitura_sensor(dados=dados_tupla)

                    hora_atual = datetime.now().strftime("%H:%M:%S")
                    ph_val = dados_tupla[1]
                    ec_val = dados_tupla[2]
                    temp_agua_val = dados_tupla[4]

                    # Atualiza mini cards
                    metric_ph.metric("pH", f"{ph_val:.2f}")
                    metric_ec.metric("EC", f"{ec_val:.2f}")
                    metric_temp.metric("Temp. Água", f"{temp_agua_val:.1f} °C")

                    historico_tempo_real.append({
                        "Horário": hora_atual,
                        "pH": ph_val,
                        "EC": ec_val,
                        "Temp Água (°C)": temp_agua_val,
                    })

                    # Atualiza mini gráfico
                    df_chart = pd.DataFrame(historico_tempo_real).set_index("Horário")
                    chart_placeholder.line_chart(df_chart[["pH", "EC"]], height=200)

                    status_box.write(
                        f"🟢 `[{hora_atual}]` **Bancada {b_id}** -> "
                        f"pH: `{ph_val}` | EC: `{ec_val}` | Temp: `{temp_agua_val}°C`"
                    )

                time.sleep(intervalo)
                barra_progresso.progress(i / qtd_leituras)
                total_processado += len(ids_para_rodar)

            # Finalizou o loop: grava o resultado e desativa a flag de execução
            st.session_state.simulando = False
            st.session_state.ultimo_resultado = {
                "status": "cancelado" if cancelado else "sucesso",
                "total": total_processado,
                "historico": historico_tempo_real,
            }

            # 💡 FORÇA O STREAMLIT A REAVALIAR A TELA E LIBERAR OS BOTÕES
            st.rerun()

st.divider()

# Indicadores de Estado do Sistema
col_a, col_b, col_c = st.columns(3)
col_a.metric("Ambiente Detectado", ENV_ATUAL.upper())
col_b.metric("Perfil de Acesso", usuario.get("role", "N/A").upper())
col_c.metric("Status da Execução", "EM ANDAMENTO" if st.session_state.simulando else "PARADO")