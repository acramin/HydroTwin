from __future__ import annotations

import streamlit as st

from hydrotwin import (
    get_current_user,
    require_page_access,
    criar_usuario,
    obter_todos_usuarios,
    get_access_code,
    logger
)


logger.debug("7_🪪_Controle_de_Acesso.py")


# Configuração da página
st.set_page_config(
    page_title="Controle de Acesso", layout="wide", page_icon="🌱"
)

st.title("🪪 Controle de Acesso")

# ==========================================
# 🔐 Autenticação e Permissão
# ==========================================
usuario = get_current_user()
if usuario is None:
    st.error("❌ Você precisa estar autenticado para acessar esta página.")
    st.stop()

require_page_access(usuario, "Controle de Acesso")

# Organização por Abas
tab_listar, tab_cadastrar = st.tabs(
    ["📋 Usuários Cadastrados", "➕ Novo Usuário"]
)

# ==========================================
# TAB 1: LISTAR E GERENCIAR USUÁRIOS
# ==========================================
with tab_listar:
    st.header(
        "Usuários Cadastrados",
        help="Visualize e gerencie usuários do sistema de monitoramento.",
    )
    
    # usar obter_todos_usuarios() para listar todos os usuários cadastrados
    usuarios = obter_todos_usuarios()
    for usuario in usuarios:
        st.write(f"• {usuario['email']} ({usuario['role']})")


# ==========================================
# TAB 2: CADASTRO DE NOVO USUÁRIO
# ==========================================
with tab_cadastrar:
    st.header(
        "Cadastrar Novo Usuário",
        help="Crie um novo usuário e libere o código de acesso.",
    )

    with st.form("register_form", clear_on_submit=True):
        email = st.text_input("E-mail do Novo Usuário", placeholder="ex: joao.silva@exemplo.com")
        role = st.selectbox("Função do Usuário", options=["viewer", "admin"], index=0)
        btn_cadastro = st.form_submit_button(
            "Enviar email", width='stretch'
        )

    if btn_cadastro:
        if not email:
            st.warning("⚠️ Informe o e-mail do novo usuário.")
        else:
            criar_usuario(email, role=role)
            st.success(f"✅ Código de cadastro enviado para {email}.")