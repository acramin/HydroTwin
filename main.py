import streamlit as st
import threading
import asyncio

from hydrotwin import (
    get_current_user,
    bootstrap_auth,
    logout_user,
    get_allowed_pages,
    obter_status_comunicacao,
    conectar_db, 
    main as iniciar_comunicacao,
    logger
)

try:
    loop = asyncio.get_running_loop()
    def handle_async_exception(loop, context):
        exception = context.get("exception")
        logger.critical(f"Exceção no Asyncio: {context.get('message')}", exc_info=exception)
    loop.set_exception_handler(handle_async_exception)
except RuntimeError:
    pass

@st.cache_resource
def iniciar_backend_global():
    logger.info("Iniciando thread global do backend HydroTwin...")
    backend_thread = threading.Thread(target=iniciar_comunicacao, daemon=True, name="BackendMain")
    backend_thread.start()
    return True

iniciar_backend_global()

conn = conectar_db()

# Configurar página
st.set_page_config(page_title="Hydroponic Monitor", layout="wide", page_icon="🌱")

# Bootstrap de autenticação
bootstrap_auth()

# Definir páginas públicas (sem restrição de login)
home = st.Page("app/pages/1_👋_HydroTwin.py", title="HydroTwin")
faq = st.Page("app/pages/5_❓_FAQ.py", title="FAQ")

# Definir páginas restritas (exigem login)
controle_bancadas = st.Page(
    "app/pages/2_🌿_Painel_de_Controle_-_Bancadas.py", 
    title="Painel de Controle | Bancadas"
)
visao_geral = st.Page(
    "app/pages/3_📊_Visão_Geral.py", 
    title="Monitoramento | Visão Geral"
)
monitoramento_detalhado = st.Page(
    "app/pages/4_🔬_Monitoramento_Detalhado.py", 
    title="Monitoramento | Detalhado"
)

# Obter usuário atual
usuario = get_current_user()

# Construir lista de páginas baseada em autenticação
if usuario is None:
    # Usuário não autenticado: apenas Home e FAQ
    pages = [home, faq]
else:
    # Usuário autenticado: Home + FAQ + páginas da role
    pages = [home, faq]
    
    user_role = usuario.get("role", "viewer")
    allowed_pages = get_allowed_pages(user_role)
    
    # Adicionar páginas permitidas pela role
    if "Painel de Controle - Bancadas" in allowed_pages:
        pages.append(controle_bancadas)
    if "Visão Geral" in allowed_pages:
        pages.append(visao_geral)
    if "Monitoramento Detalhado" in allowed_pages:
        pages.append(monitoramento_detalhado)

# Renderizar user badge na sidebar
if usuario is not None:
    with st.sidebar:
        status, ultima = obter_status_comunicacao(conn)
        col1, col2 = st.columns([2,1])
        with col1:
            st.caption(f"👤 {usuario['username']} ({usuario['role']})")
        with col2:
            if st.button("🚪 Sair", use_container_width=True):
                logout_user()
                st.rerun()
        with st.expander("🔌 Status de Comunicação", expanded=True):
            st.write(f"**Status:** {status}")
            if ultima is not None:
                st.write(f"**Último Dado Recebido:** {ultima.strftime('%Y-%m-%d %H:%M:%S')}")

# Renderizar navegação
pg = st.navigation(pages)
pg.run()
