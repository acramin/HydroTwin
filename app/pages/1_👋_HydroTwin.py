from __future__ import annotations

import streamlit as st
from hydrotwin import (
    autenticar_usuario,
    finalizar_cadastro,
    get_current_user,
    logger,
    set_current_user,
    logout_user,
)

logger.debug("1_👋_HydroTwin.py")

# Configuração da página
st.set_page_config(
    page_title="HydroTwin - Monitoramento Hidropônico",
    layout="wide",
    page_icon="🌱",
)

# Bootstrap do sistema de autenticação
usuario = get_current_user()

# ==========================================
# 🌿 CABEÇALHO & AUTENTICAÇÃO
# ==========================================
st.title("🌱 HydroTwin")

if usuario is None:
    # Centraliza o formulário de autenticação na tela
    col_left, col_center, col_right = st.columns([1, 2, 1])

    with col_center:
        with st.container(border=True):
            st.subheader("🔐 Acesse a Plataforma")
            st.caption("Faça login ou ative sua conta com um código de convite.")

            tab_login, tab_cadastro = st.tabs(["🔑 Entrar", "✍️ Criar Conta"])

            # --- TAB LOGIN ---
            with tab_login:
                with st.form("login_form", clear_on_submit=False):
                    username = st.text_input("Usuário", placeholder="ex: master")
                    password = st.text_input("Senha", type="password")
                    btn_login = st.form_submit_button(
                        "Entrar", width='stretch', type="primary"
                    )

                if btn_login:
                    if not username or not password:
                        st.warning("⚠️ Preencha o usuário e a senha.")
                    else:
                        usuario_auth = autenticar_usuario(username, password)
                        if usuario_auth is None:
                            st.error("❌ Usuário ou senha inválidos.")
                        else:
                            set_current_user(usuario_auth)
                            st.success(f"✅ Bem-vindo de volta, {usuario_auth['username']}!")
                            st.rerun()

            # --- TAB CADASTRO ---
            with tab_cadastro:
                with st.form("register_form", clear_on_submit=True):
                    code_acesso = st.text_input("Código de Convite *", placeholder='ex: abc45')
                    novo_username = st.text_input("Escolha seu Nome de Usuário *", placeholder="ex: joao.silva")
                    nova_senha = st.text_input("Senha *", type="password")
                    confirmar_senha = st.text_input("Confirmar Senha *", type="password")
                    
                    btn_cadastro = st.form_submit_button(
                        "Criar Conta", width='stretch'
                    )

                if btn_cadastro:
                    username_normalizado = novo_username.strip()
                    code_normalizado = code_acesso.strip()

                    if not code_normalizado:
                        st.warning("⚠️ Informe o código de convite que você recebeu.")
                    elif not username_normalizado:
                        st.warning("⚠️ Informe um nome de usuário.")
                    elif username_normalizado.lower() == "admin":
                        st.warning("⚠️ O nome de usuário 'admin' é reservado.")
                    elif len(nova_senha) < 6:
                        st.warning("⚠️ A senha deve ter pelo menos 6 caracteres.")
                    elif nova_senha != confirmar_senha:
                        st.warning("⚠️ As senhas não coincidem.")
                    else:
                        try:
                            # Converte o convite em usuário ativo
                            finalizar_cadastro(
                                code=code_normalizado, 
                                username=username_normalizado, 
                                password=nova_senha
                            )
                            
                            # Autentica e realiza login automaticamente
                            usuario_auth = autenticar_usuario(username_normalizado, nova_senha)
                            set_current_user(usuario_auth)
                            st.success("✅ Conta criada com sucesso! Entrando...")
                            st.rerun()
                        except ValueError as ve:
                            st.warning(f"⚠️ {ve}")
                        except Exception as e:
                            st.error(f"❌ Erro ao criar conta: {e}")

else:
    # Usuário Logado - Exibe Card de Perfil
    with st.container(border=True):
        col_u1, col_u2 = st.columns([3, 1])
        with col_u1:
            st.markdown(
                f"👤 **Usuário Autenticado:** `{usuario.get('username')}` | "
                f"Perfil: **{usuario.get('role', 'viewer').upper()}**"
            )
        with col_u2:
            if st.button("🚪 Sair / Logout", width='stretch'):
                logout_user()
                st.rerun()

st.divider()

# ==========================================
# 📘 APRESENTAÇÃO DO PROJETO (TCC SIMPLIFICADO)
# ==========================================

st.header("💡 O que é o HydroTwin?")
st.markdown(
    """
    O **HydroTwin** é uma plataforma que aplica o conceito de **Gêmeo Digital (Digital Twin)** à agricultura urbana e à hidroponia em técnica NFT (*Nutrient Film Technique*). 
    
    A proposta conecta o cultivo físico do campo a um modelo digital no computador ou celular, 
    permitindo monitorar e controlar o ambiente das plantas em tempo real de forma automatizada.
    """
)

# Métricas de Destaque
m1, m2, m3, m4 = st.columns(4)
m1.metric("Economia de Água", "Até 90%", "vs. Solo Tradicional")
m2.metric("Monitoramento", "24/7", "Tempo Real")
m3.metric("Foco", "NFT", "Hidroponia")
m4.metric("Tecnologia", "IoT + IA", "Baixo Custo")

st.markdown("---")

# Seção: Como Funciona
st.subheader("⚙️ Como Funciona o Sistema?")

col_card1, col_card2, col_card3 = st.columns(3)

with col_card1:
    with st.container(border=True, height="stretch"):
        st.markdown("### 📡 1. Coleta de Dados")
        st.write(
            "Sensores medem continuamente os parâmetros vitais do cultivo:\n"
            "* **Qualidade da Água:** pH e Condutividade Elétrica (EC)\n"
            "* **Ambiente:** Temperatura, Umidade e Luminosidade\n"
            "* **Nível do Tanque:** Reservatório de nutrientes"
        )

with col_card2:
    with st.container(border=True, height="stretch"):
        st.markdown("### 🧠 2. Processamento")
        st.write(
            "Microcontroladores (como ESP32/Arduino) e minicomputadores (Raspberry Pi) "
            "processam as leituras e calculam a necessidade de ajustes na solução nutritiva."
        )

with col_card3:
    with st.container(border=True, height="stretch"):
        st.markdown("### 🔄 3. Ação & Resposta")
        st.write(
            "O sistema dispara alertas, aciona dosadores de correção ou bombas d'água "
            "automaticamente para garantir a saúde das plantas sem desperdícios."
        )

st.markdown("---")

# Seção: Arquitetura NFT
col_img, col_txt = st.columns([1.2, 1])

with col_img:
    st.image(
        "https://raw.githubusercontent.com/acramin/HydroTwin/refs/heads/dev/app/assets/esquema_NFT.png",
        caption="Esquema da Técnica de Fluxo Laminar de Nutrientes (NFT) integrada ao HydroTwin",
        width='stretch',
    )

with col_txt:
    st.subheader("🌱 A Técnica NFT & Automação")
    st.markdown(
        """
        Na técnica **NFT**, as raízes das plantas recebem uma fina lâmina de água enriquecida com nutrientes. 
        
        **Por que automatizar com o HydroTwin?**
        * **Sem surpresas:** Mudanças bruscas no pH ou na temperatura da água são detectadas na hora.
        * **Acessibilidade:** Desenvolvido com hardware acessível para pequenos e médios produtores.
        * **Sustentabilidade:** Uso circular da água e insumos, evitando contaminação do solo e perdas na produção.
        """
    )

st.markdown("---")

# Rodapé
st.caption(
    "🌱 **HydroTwin** — Solução inteligente para hidroponia automatizada. "
    "Desenvolvido como projeto de pesquisa e inovação tecnológica."
)