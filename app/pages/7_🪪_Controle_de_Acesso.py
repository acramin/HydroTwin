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
st.caption("Gerencie os usuários do sistema, permissões de acesso e novos convites.")

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
                "🔎 Buscar por e-mail ou nome",
                placeholder="Digite para filtrar...",
                label_visibility="collapsed",
            )
        with col_filtro_role:
            filtro_role = st.selectbox(
                "Filtrar por Função",
                options=["Todos", "admin", "viewer"],
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
                "role": "Função (Role)",
            }
            
            cols_presentes = [c for c in colunas_map.keys() if c in df_usuarios.columns]
            df_display = df_usuarios[cols_presentes].rename(columns=colunas_map)

            st.dataframe(
                df_display,
                width='stretch',
                hide_index=True,
                column_config={
                    "Nome de Usuário": st.column_config.TextColumn("Nome de Usuário", width="medium"),
                    "E-mail": st.column_config.TextColumn("E-mail", width="large"),
                    "Função (Role)": st.column_config.TextColumn("Função", width="medium"),
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
            
    st.subheader("➕ Enviar Novo Convite")
    st.caption("Gere um convite temporário e envie o código de liberação para o e-mail informado.")

    col_form, col_info = st.columns([2, 1], gap="large")

    with col_form:
        with st.container(border=True):
            with st.form("register_form", clear_on_submit=True):
                email = st.text_input(
                    "E-mail do Destinatário *",
                    placeholder="ex: joao.silva@exemplo.com",
                    help="O código de primeiro acesso será gerado para este e-mail.",
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
                    st.error(f"❌ Erro ao gerar convite para `{email}`: {e}")

    # --- Card de Informações sobre Permissões ---
    with col_info:
        with st.container(border=True):
            st.markdown("### ℹ️ Sobre as Funções")
            st.markdown(
                """
                **👁️ Viewer (Visualizador)**
                * Acesso de leitura aos Dashboards e Monitoramento.
                * Sem permissão para alterar configurações ou cadastrar dados.

                **👑 Admin (Administrador)**
                * Acesso total a todas as telas do sistema.
                * Permissão para gerenciar bancadas, simulador e novos usuários.
                """
            )