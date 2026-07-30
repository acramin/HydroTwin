from __future__ import annotations

import streamlit as st

from hydrotwin import (
    get_current_user,
    get_bancadas,
    logger
)

logger.debug("3_📊_Visão_Geral.py")

from app.components.visao_geral import (
    get_last_status,
    get_kpis,
    get_alertas
)

# Configuração da Página
st.set_page_config(page_title="Hydroponic Monitor", layout="wide", page_icon="🌱")

# ==========================================
# 📊 Visão Geral
# ==========================================
st.title("📊 Visão Geral")

# 🔐 Autenticação
usuario = get_current_user()
if usuario is None:
    st.error("❌ Você precisa estar autenticado para acessar esta página.")
    st.stop()

status_bancadas = get_last_status()

# Validação de bancadas existentes
if not status_bancadas:
    role = usuario.get("role")
    if role == "admin":
        st.info("Cadastre uma bancada para acessar a visão geral.")
    else:
        st.info("Aguarde até que o administrador cadastre uma bancada para acessar a visão geral.")
    st.stop()

st.caption("Status operacional em tempo real, indicadores rápidos e alertas do sistema.")

# ==========================================
# 🟢 1. Status das Bancadas
# ==========================================
st.subheader("Status das Bancadas")

# Ordenação alfabética das bancadas
bancadas_ordenadas = sorted(status_bancadas.keys())
cols_status = st.columns(min(4, len(bancadas_ordenadas)))

for idx, nome_bancada in enumerate(bancadas_ordenadas):
    info = status_bancadas[nome_bancada]
    status_txt = info["status"]
    atualizado_em = info["atualizado_em"]

    # Mapeamento de emojis por status
    if status_txt == "Sem dados":
        emoji = "⚪"
    elif "Saudável" in status_txt or "Normal" in status_txt:
        emoji = "🟢"
    elif "Atenção" in status_txt:
        emoji = "🟡"
    else:
        emoji = "🔴"

    with cols_status[idx % len(cols_status)]:
        with st.container(border=True):
            st.metric(nome_bancada.capitalize(), f"{emoji} {status_txt}")
            st.caption(f"Atualizado: {atualizado_em}")

st.divider()

# ==========================================
# 📈 2. Indicadores Gerais (KPIs)
# ==========================================
st.subheader("Indicadores Gerais por Bancada")

# Mapeamento de rótulos e unidades de exibição
ROTULOS_KPIS = {
    "ph": ("pH", ""),
    "ec": ("EC", "mS/cm"),
    "temperatura_agua": ("Temp. Água", "°C"),
    "temperatura_ambiente": ("Temp. Ambiente", "°C"),
    "umidade": ("Umidade", "%"),
    "nivel_tanque": ("Nível Tanque", ""),
    "luminosidade": ("Luminosidade", "lux"),
}

bancadas_cadastradas = get_bancadas() or []

for bancada in sorted(bancadas_cadastradas, key=lambda x: x[1]):
    if not bancada or not bancada[0]:
        continue

    bancada_id, nome = bancada[0], bancada[1]
    kpis = get_kpis(bancada_id)

    with st.container(border=True):
        st.markdown(f"### 📍 {nome.capitalize()}")

        if not kpis:
            st.info(
                f"Nenhum KPI calculado ainda para a bancada **{nome}**. "
                "Assim que as próximas leituras brutas entrarem, os cálculos serão gerados automaticamente."
            )
        else:
            cols_kpi = st.columns(min(4, len(kpis)))
            for i, (chave, valor) in enumerate(kpis.items()):
                rotulo, unidade = ROTULOS_KPIS.get(chave, (chave.capitalize().replace("_", " "), ""))

                # Formatação de valores numéricos
                if isinstance(valor, (int, float)):
                    texto_valor = f"{valor:.2f} {unidade}".strip()
                else:
                    texto_valor = str(valor) if valor is not None else "N/A"

                with cols_kpi[i % len(cols_kpi)]:
                    st.metric(rotulo, texto_valor)

st.divider()

# ==========================================
# 🚨 3. Alertas Ativos
# ==========================================
st.subheader("Alertas Ativos")

alertas = get_alertas()

if not alertas:
    st.success("🟢 Nenhum alerta ativo no momento!")
else:
    for alerta in alertas:
        texto = alerta.get("texto_formatado", alerta.get("mensagem", ""))
        nivel = alerta.get("nivel", "atencao").lower()

        if nivel in ["critico", "erro", "error"]:
            st.error(f"🚨 {texto}")
        else:
            st.warning(f"⚠️ {texto}")