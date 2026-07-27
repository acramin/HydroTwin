import streamlit as st
from hydrotwin import (
    get_current_user,
    set_current_user,
    bootstrap_auth,
    autenticar_usuario,
    criar_usuario,
)

st.set_page_config(page_title="Hydroponic Monitor", layout="wide", page_icon="🌱")

st.title("🌱 HydroTwin")

# Bootstrap de autenticação
bootstrap_auth()
usuario = get_current_user()

# Se não está autenticado, mostrar formulário de login/cadastro
if usuario is None:
    st.subheader("Bem-vindo ao HydroTwin")
    
    with st.expander("Para acessar todas as funcionalidades, faça login ou crie uma nova conta."):
        tab_login, tab_cadastro = st.tabs(["🔑 Entrar", "✍️ Criar Conta"])
    
    with tab_login:
        with st.form("login_form"):
            username = st.text_input("Usuário", placeholder="ex: master")
            password = st.text_input("Senha", type="password")
            submitted = st.form_submit_button("Entrar", use_container_width=True)

        if submitted:
            usuario_auth = autenticar_usuario(username, password)
            if usuario_auth is None:
                st.error("❌ Usuário ou senha inválidos.")
            else:
                set_current_user(usuario_auth)
                st.success(f"✅ Bem-vindo, {usuario_auth['username']}!")
                st.rerun()

    with tab_cadastro:
        with st.form("register_form"):
            novo_username = st.text_input("Novo usuário", placeholder="ex: joao.silva")
            nova_senha = st.text_input("Senha", type="password")
            confirmar_senha = st.text_input("Confirmar senha", type="password")
            submitted = st.form_submit_button("Criar usuário", use_container_width=True)

        if submitted:
            username_normalizado = novo_username.strip()
            if not username_normalizado:
                st.warning("⚠️ Informe um nome de usuário.")
            elif username_normalizado.lower() == "admin":
                st.warning("⚠️ O usuário admin é reservado ao administrador.")
            elif len(nova_senha) < 6:
                st.warning("⚠️ A senha deve ter pelo menos 6 caracteres.")
            elif nova_senha != confirmar_senha:
                st.warning("⚠️ As senhas não conferem.")
            else:
                try:
                    criar_usuario(username_normalizado, nova_senha, role="viewer")
                    usuario_auth = autenticar_usuario(username_normalizado, nova_senha)
                    set_current_user(usuario_auth)
                    st.success("✅ Usuário criado com sucesso! Você já está logado.")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Erro ao criar usuário: {str(e)}")
    st.divider()

# Mostrar conteúdo principal (visível para todos)
st.markdown(
    """

    O HydroTwin é um projeto que une tecnologia e agricultura para tornar o cultivo de alimentos mais eficiente, sustentável e acessível.

    Hoje, grande parte da agricultura ainda depende de fatores difíceis de controlar, como clima, disponibilidade de água e manejo manual. Isso pode gerar desperdícios, perda de produção e custos elevados.

    Pensando nisso, o HydroTwin propõe uma solução baseada em cultivo hidropônico automatizado, onde as plantas crescem sem solo e recebem exatamente os nutrientes que precisam, na quantidade certa.

    ## 💧 Por que isso importa?

    A agricultura tradicional consome uma enorme quantidade de água. Já sistemas hidropônicos conseguem reduzir esse consumo drasticamente, reutilizando a água em ciclos fechados e evitando desperdícios.

    Além disso, o controle mais preciso do ambiente ajuda a:

    - Reduzir perdas na produção
    - Melhorar a qualidade dos alimentos
    - Produzir mais em menos espaço
    - Diminuir o impacto ambiental
    
    ## 🤖 Como o sistema funciona?

    O HydroTwin utiliza sensores e automação para monitorar continuamente o cultivo.

    Na prática, isso significa que o sistema acompanha fatores importantes como:

    - Qualidade da água
    - Temperatura
    - Fluxo de nutrientes
    - Condições do ambiente

    Com base nesses dados, o próprio sistema pode tomar decisões automaticamente, ajustando o que for necessário para manter as plantas sempre nas melhores condições.
    
    ![Diagrama do sistema HydroTwin](https://raw.githubusercontent.com/acramin/hydrotwin/refs/heads/main/assets/esquema_NFT.png)

    ## 📡 Tecnologia a favor do produtor

    Um dos principais objetivos do projeto é tornar essa tecnologia acessível, principalmente para pequenos e médios produtores.

    Para isso, o HydroTwin combina:

    - Sensores de baixo custo
    - Microcontroladores (como Arduino)
    - Computação embarcada (como Raspberry Pi)
    - Monitoramento remoto via internet

    Isso permite que o produtor acompanhe tudo em tempo real, de forma simples e prática.

    ## 🌍 O que torna o HydroTwin diferente?

    Mais do que um sistema de cultivo, o HydroTwin é uma plataforma que busca:

    - Democratizar o acesso à automação agrícola
    - Reduzir desperdícios de recursos naturais
    - Aumentar a eficiência da produção
    - Levar tecnologia de ponta para o campo
    
    ## 🚀 Nosso objetivo

    Criar um sistema inteligente, automatizado e acessível, capaz de ajudar na produção de alimentos de forma mais sustentável, eficiente e confiável.
        
        
    
    """
)
