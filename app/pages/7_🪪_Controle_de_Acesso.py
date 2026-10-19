from __future__ import annotations

import pandas as pd
import streamlit as st

from hydrotwin import (
    criar_convite,
    get_current_user,
    logger,
    obter_todos_usuarios,
    require_page_access,
)

logger.debug("7_🪪_Controle_de_Acesso.py")

# Configuração da página
st.set_page_config(
    page_title="Controle de Acesso - HydroTwin",
    layout="wide",
    page_icon="🌱",
)

# ==========================================
# 🔐 Autenticação e Permissão
# ==========================================
usuario_logado = get_current_user()
if usuario_logado is None:
    st.error("❌ Você precisa estar autenticado para acessar esta página.")
    st.stop()

require_page_access(usuario_logado, "Controle de Acesso")

# Cabeçalho da Página
st.title("🪪 Controle de Acesso")
st.caption("Consulte quem tem acesso ao HydroTwin e envie convites para novas pessoas entrarem na plataforma.")

st.divider()

# Organização por Abas
tab_listar, tab_cadastrar = st.tabs(
    ["📋 Usuários Cadastrados", "➕ Novo Convite"]
)

# ==========================================
# TAB 1: LISTAR E GERENCIAR USUÁRIOS
# ==========================================
with tab_listar:
    usuarios = obter_todos_usuarios() or []

    if not usuarios:
        st.info("ℹ️ Nenhum usuário cadastrado no sistema.")
    else:
        # --- 📊 Métricas Rápidas ---
        total_usuarios = len(usuarios)
        total_admins = sum(1 for u in usuarios if u.get("role") == "admin")
        total_viewers = sum(1 for u in usuarios if u.get("role") == "viewer")

        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("Total de Usuários", total_usuarios)
        col_m2.metric("Administradores", total_admins)
        col_m3.metric("Visualizadores (Viewer)", total_viewers)

        st.markdown("---")

        # --- 🔍 Filtros de Busca ---
        col_busca, col_filtro_role = st.columns([3, 1])
        with col_busca:
            termo_busca = st.text_input(
                "🔎 Buscar usuário por e-mail ou nome",
                placeholder="Digite para filtrar...",
                label_visibility="collapsed",
            )
        with col_filtro_role:
            filtro_role = st.selectbox(
                "Filtrar por perfil de acesso",
                options=["Todos", "admin", "viewer"],
                format_func=lambda x: {"Todos": "Todos os perfis", "admin": "Administrador", "viewer": "Visualizador"}[x],
                label_visibility="collapsed",
            )

        # Filtragem dos dados
        usuarios_filtrados = usuarios
        if termo_busca:
            termo = termo_busca.lower()
            usuarios_filtrados = [
                u for u in usuarios_filtrados 
                if termo in u.get("email", "").lower() or termo in u.get("username", "").lower()
            ]
        if filtro_role != "Todos":
            usuarios_filtrados = [
                u for u in usuarios_filtrados if u.get("role") == filtro_role
            ]

        # --- 📋 Tabela de Usuários ---
        if usuarios_filtrados:
            df_usuarios = pd.DataFrame(usuarios_filtrados)
            
            # Renomear colunas para exibição amigável
            colunas_map = {
                "username": "Nome de Usuário",
                "email": "E-mail",
                "role": "Perfil de Acesso",
            }
            
            cols_presentes = [c for c in colunas_map.keys() if c in df_usuarios.columns]
            df_display = df_usuarios[cols_presentes].rename(columns=colunas_map)
            if "Perfil de Acesso" in df_display.columns:
                df_display["Perfil de Acesso"] = df_display["Perfil de Acesso"].map(
                    {"admin": "Administrador", "viewer": "Visualizador"}
                ).fillna(df_display["Perfil de Acesso"])

            st.dataframe(
                df_display,
                width='stretch',
                hide_index=True,
                column_config={
                    "Nome de Usuário": st.column_config.TextColumn("Nome de Usuário", width="medium"),
                    "E-mail": st.column_config.TextColumn("E-mail", width="large"),
                    "Perfil de Acesso": st.column_config.TextColumn("Perfil de Acesso", width="medium"),
                },
            )
        else:
            st.warning("Nenhum usuário atende aos critérios de busca.")


# ==========================================
# TAB 2: CADASTRO DE NOVO CONVITE
# ==========================================
with tab_cadastrar:
    if "sucesso_cadastro" in st.session_state:
        msg = st.session_state.pop("sucesso_cadastro")
        st.success(msg)
        st.toast("Convite enviado com sucesso!", icon="🎉")
            
    st.subheader("➕ Convidar uma pessoa")
    st.caption("Informe o e-mail e o perfil desejado. A pessoa receberá um convite para criar a própria conta.")

    col_form, col_info = st.columns([2, 1], gap="large")

    with col_form:
        with st.container(border=True):
            with st.form("register_form", clear_on_submit=True):
                email = st.text_input(
                    "E-mail do Destinatário *",
                    placeholder="ex: joao.silva@exemplo.com",
                    help="O convite será associado a este endereço de e-mail.",
                )
                
                role = st.selectbox(
                    "Função no Sistema *",
                    options=["viewer", "admin"],
                    index=0,
                    format_func=lambda x: "👑 Administrador (admin)" if x == "admin" else "👁️ Visualizador (viewer)",
                )

                st.markdown("---")
                btn_cadastro = st.form_submit_button(
                    "📧 Gerar e Enviar Convite",
                    type="primary",
                    width='stretch',
                )

        if btn_cadastro:
            if not email or "@" not in email:
                st.warning("⚠️ Por favor, informe um endereço de e-mail válido.")
            else:
                try:
                    with st.spinner("Gerando código de convite e enviando e-mail..."):
                        criar_convite(email, role=role)
                    
                    st.session_state["sucesso_cadastro"] = f"✅ Convite para `{email}` gerado e enviado com sucesso!"
                    st.rerun()

                except ValueError as ve:
                    st.warning(f"⚠️ {ve}")
                except Exception as e:
                    st.error("❌ Não foi possível enviar o convite. Confira as configurações de e-mail e tente novamente.")

    # --- Card de Informações sobre Permissões ---
    with col_info:
        with st.container(border=True):
            st.markdown("### ℹ️ Sobre as Funções")
            st.markdown(
                """
                **👁️ Visualizador (`viewer`)**
                * Pode consultar as telas de acompanhamento, gráficos e alertas.
                * Não pode realizar ações administrativas.

                **👑 Administrador (`admin`)**
                * Pode gerenciar bancadas, filetes, convites e usuários.
                * O simulador só fica disponível em ambiente de desenvolvimento.
                """
            )