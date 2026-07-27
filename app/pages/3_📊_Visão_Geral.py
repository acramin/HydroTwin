import streamlit as st

from hydrotwin import (
    get_current_user,
    get_bancadas
)

from app.components.visao_geral import (
    get_last_status,
    get_kpis,
    get_alertas
)

st.set_page_config(page_title="Hydroponic Monitor", layout="wide", page_icon="🌱")

# =========================
# 📊 Visão Geral
# =========================

st.title("📊 Visão Geral")

usuario = get_current_user()
if usuario is None:
    st.error("❌ Você precisa estar autenticado para acessar esta página.")
    st.stop()

status = get_last_status()

if len(status) == 0 and usuario["role"] == "admin":
    st.info("Cadastre uma bancada para acessar a visão geral.")
    st.stop()

if len(status) == 0 and usuario["role"] == "viewer":
    st.info("Aguarde até que admin cadastre uma bancada para acessar a visão geral.")
    st.stop()

st.caption(f"Status atual das bancadas, indicadores rápidos e alertas ativos. Última atualização: {status.get('atualizado_em', 'N/A')}")

# STATUS
st.subheader("Status das Bancadas")

status.pop("atualizado_em", None)  # Remove o timestamp do status para exibir só as bancadas

if not status:
    st.info("Nenhuma bancada cadastrada ainda.")
else:
    bancadas = list(status.keys())
    bancadas.sort()  # Ordenar alfabeticamente
    status = {b: status[b] for b in bancadas}  # Reordenar o dicionário com as bancadas ordenadas
    colunas = st.columns(min(4, len(status)))
    for i, (b, s) in enumerate(status.items()):
        emoji = "⚪" if s == "Sem dados" else "🟢" if "Saudável" in s else "🟡" if "Atenção" in s else "🔴" 
        colunas[i % len(colunas)].metric(b.capitalize(), f"{emoji} {s}")

# KPIs
st.subheader("Indicadores Gerais")

for bancada_id, nome, *_ in sorted(get_bancadas(), key=lambda x: x[0]):
    kpis = get_kpis(bancada_id, nome)
    
    if len(kpis.get(nome, {})) == 0:
        st.info(f"Nenhum KPI calculado ainda para a bancada {nome}. Assim que as próximas leituras brutas entrarem, os cálculos serão gerados automaticamente.")
    
    if kpis:
        st.markdown(f"**{nome.capitalize()}**")
        colunas = st.columns(min(4, len(kpis[nome])))
        for i, (k, v) in enumerate(kpis[nome].items()):
            colunas[i % len(colunas)].metric(k.capitalize().replace("_", " "), f"{v:.2f}" if isinstance(v, (int, float)) else v)

#Alertas ativos
alertas = get_alertas()
st.subheader("Alertas Ativos")

if not alertas:
    st.success("Nenhum alerta ativo!")
else:
    for alerta in alertas:
        st.warning(alerta)
