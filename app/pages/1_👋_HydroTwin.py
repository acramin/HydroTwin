from __future__ import annotations

from pathlib import Path

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
# 🌱 APRESENTAÇÃO DO PROJETO
# ==========================================

st.header("🌱 Monitoramento e automação para hidroponia NFT")
st.markdown(
    """
    O **HydroTwin** é um sistema de monitoramento e automação aplicado a um cultivo
    hidropônico que utiliza a técnica **NFT** (*Nutrient Film Technique*). Ele reúne
    a aquisição de dados por sensores, o processamento local e uma interface para
    acompanhar as bancadas e seus indicadores operacionais.

    O projeto combina um **Arduino Mega**, responsável pela leitura dos sensores e
    pelo acionamento de atuadores, com um **Raspberry Pi**, que recebe as leituras,
    armazena os dados em **SQLite** e disponibiliza a interface desenvolvida em
    **Streamlit**.
    """
)

m1, m2, m3 = st.columns(3)
m1.metric("Técnica de cultivo", "NFT", "Recirculação da solução nutritiva")
m2.metric("Processamento", "Local", "Raspberry Pi + SQLite")
m3.metric("Interface", "Streamlit", "Painéis e histórico de leituras")

st.divider()
st.subheader("⚙️ Como o sistema funciona")

col1, col2, col3 = st.columns(3)
with col1:
    with st.container(border=True, height="stretch"):
        st.markdown("### 📡 1. Aquisição")
        st.write(
            "O firmware lê pH, condutividade elétrica (EC), temperatura da água, "
            "temperatura e umidade do ar, luminosidade e estado da boia de nível "
            "em cada uma das duas bancadas conectadas ao Arduino."
        )
with col2:
    with st.container(border=True, height="stretch"):
        st.markdown("### 🗃️ 2. Supervisão")
        st.write(
            "O Raspberry Pi recebe as mensagens do Arduino, registra as leituras "
            "brutas no banco SQLite e executa o processamento periódico. A aplicação "
            "calcula estatísticas, avalia o estado operacional com base em pH e EC "
            "e analisa anomalias e tendências nas séries de dados."
        )
with col3:
    with st.container(border=True, height="stretch"):
        st.markdown("### 🔧 3. Atuação")
        st.write(
            "O Arduino controla a iluminação e pode acionar bombas de nutrientes "
            "conforme a lógica embarcada e os parâmetros de cultura recebidos. "
            "O painel permite acompanhar o sistema; nem toda variável monitorada "
            "possui correção automática."
        )

st.divider()
st.subheader("🧪 O que é monitorado?")
sensores = [
    ("pH", "Indicador da acidez/alcalinidade da solução."),
    ("EC", "Condutividade elétrica usada como indicador da concentração iônica."),
    ("Temperatura da água", "Temperatura da solução nutritiva."),
    ("Temperatura e umidade do ar", "Condições do ambiente ao redor do cultivo."),
    ("Luminosidade", "Leitura do sensor de luz instalado na bancada."),
    ("Nível do tanque", "Estado informado pela boia de nível."),
]
cols = st.columns(3)
for i, (nome, descricao) in enumerate(sensores):
    with cols[i % 3]:
        with st.container(border=True, height="stretch"):
            st.markdown(f"**{nome}**")
            st.caption(descricao)

st.divider()
col_img, col_txt = st.columns([1.1, 1])
with col_img:
    caminho_esquema = Path(__file__).resolve().parents[1] / "assets" / "esquema_NFT.png"
    if caminho_esquema.exists():
        st.image(
            str(caminho_esquema),
            caption="Esquema ilustrativo da técnica hidropônica NFT.",
            width="stretch",
        )
    else:
        st.info("O esquema NFT não foi encontrado em app/assets/esquema_NFT.png.")
with col_txt:
    st.subheader("🌿 Por que NFT?")
    st.markdown(
        """
        Na técnica **NFT**, uma lâmina de solução nutritiva circula pelos canais
        de cultivo e entra em contato com as raízes. O HydroTwin foi desenvolvido
        para apoiar a supervisão desse processo por meio de leituras, histórico,
        indicadores operacionais e recursos de automação embarcada.

        **Importante:** o software não é um modelo de simulação de um gêmeo digital
        nem utiliza inteligência artificial para prever o crescimento das plantas.
        As análises implementadas são baseadas em limites, estatística de leituras
        recentes e comparação de médias.
        """
    )

st.divider()
st.subheader("🧭 Explore a plataforma")
st.markdown(
    """
    - **Painel de Controle – Bancadas:** cadastro e gerenciamento de bancadas,
      culturas, filetes e associação a controladores.
    - **Visão Geral:** resumo do estado operacional e dos dados processados.
    - **Monitoramento Detalhado:** estatísticas, histórico, anomalias e tendências.
    - **FAQ:** explicações sobre funcionamento, leituras, automação e limitações.
    """
)
st.caption(
    "HydroTwin — projeto acadêmico de monitoramento e automação local para cultivo hidropônico."
)