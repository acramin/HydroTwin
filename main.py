import asyncio
import threading
from hydrotwin import (
    bootstrap_auth,
    conectar_db,
    get_allowed_pages,
    get_current_user,
    logger,
    logout_user,
    main as iniciar_comunicacao,
    obter_status_comunicacao,
)
import streamlit as st

logger.debug("main.py")

# --- TRATAMENTO ASYNCIO ---
try:
    loop = asyncio.get_running_loop()

    def handle_async_exception(loop, context):
        exception = context.get("exception")
        logger.critical(
            f"Exceção no Asyncio: {context.get('message')}", exc_info=exception
        )

    loop.set_exception_handler(handle_async_exception)
except RuntimeError:
    pass

# --- INITIALIZATION ---
@st.cache_resource
def iniciar_backend_global():
    logger.info("Iniciando thread global do backend HydroTwin...")
    backend_thread = threading.Thread(
        target=iniciar_comunicacao, daemon=True, name="BackendMain"
    )
    backend_thread.start()
    return True

iniciar_backend_global()
conn = conectar_db()

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Hydroponic Monitor", layout="wide", page_icon="🌱"
)

# Bootstrap de autenticação
bootstrap_auth()

# --- DEFINIÇÃO DAS PÁGINAS ---
home = st.Page("app/pages/1_👋_HydroTwin.py", title="HydroTwin")
faq = st.Page("app/pages/5_❓_FAQ.py", title="FAQ")

controle_bancadas = st.Page(
    "app/pages/2_🌿_Painel_de_Controle_-_Bancadas.py",
    title="Painel de Controle | Bancadas",
)
visao_geral = st.Page(
    "app/pages/3_📊_Visão_Geral.py", title="Monitoramento | Visão Geral"
)
monitoramento_detalhado = st.Page(
    "app/pages/4_🔬_Monitoramento_Detalhado.py",
    title="Monitoramento | Detalhado",
)
simulador = st.Page("app/pages/6_🕹️_Simulador.py", title="Simulador")

acessos = st.Page("app/pages/7_🪪_Controle_de_Acesso.py", title="Controle de Acesso")

usuario = get_current_user()

# --- CONSTRUÇÃO DO MENU NAVEGÁVEL (AGRUPADO) ---
if usuario is None:
    # Usuário não autenticado: exibição mínima
    pages_config = {"📌 Principal": [home], "❓ Suporte": [faq]}
else:
    # Usuário autenticado: monta dicionário estruturado por seções
    user_role = usuario.get("role", "viewer")
    allowed_pages = get_allowed_pages(user_role)

    pages_config = {}

    # 1. Seção Principal
    pages_config["📌 Principal"] = [home]

    # 2. Seção de Monitoramento Operacional
    secao_monitoramento = []
    if "Visão Geral" in allowed_pages:
        secao_monitoramento.append(visao_geral)
    if "Monitoramento Detalhado" in allowed_pages:
        secao_monitoramento.append(monitoramento_detalhado)

    if secao_monitoramento:
        pages_config["📊 Monitoramento"] = secao_monitoramento

    # 3. Seção de Gestão e Controle
    secao_gestao = []
    if "Painel de Controle - Bancadas" in allowed_pages:
        secao_gestao.append(controle_bancadas)
    if "Controle de Acesso" in allowed_pages:
        secao_gestao.append(acessos)

    if secao_gestao:
        pages_config["⚙️ Gestão"] = secao_gestao

    # 4. Seção de Ajuda / Suporte
    pages_config["❓ Ajuda"] = [faq]

    # 5. Seção de Ferramentas / Dev (Só aparece se estiver liberado para Role + ENV)
    if "Simulador" in allowed_pages:
        pages_config["🛠️ Ferramentas"] = [simulador]

# --- USER BADGE & SIDEBAR ---
if usuario is not None:
    with st.sidebar:
        status, ultima = obter_status_comunicacao(conn)
        col1, col2 = st.columns([2, 1])
        with col1:
            st.caption(f"👤 {usuario['username']} ({usuario['role']})")
        with col2:
            if st.button("🚪 Sair", width='stretch'):
                logout_user()
                st.rerun()

        with st.expander("🔌 Status de Comunicação", expanded=True):
            st.write(f"**Status:** {status}")
            if ultima is not None:
                st.write(
                    f"**Último Dado Recebido:** {ultima.strftime('%Y-%m-%d %H:%M:%S')}"
                )

# --- RENDERIZAÇÃO DA NAVEGAÇÃO ---
pg = st.navigation(pages_config)
pg.run()