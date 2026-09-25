from __future__ import annotations

from datetime import date
import time
import streamlit as st

from hydrotwin import (
    enfileirar_envio,
    get_bancadas,
    get_culturas,
    get_current_user,
    inserir_bancada,
    inserir_filete,
    limpar_status_envio,
    obter_status_envio,
    require_page_access,
    obter_controladores_com_vagas,
    associar_bancada_ao_controlador,
    get_controladores,
    logger
)

logger.debug("2_🌿_Painel_de_Controle_-_Bancadas.py")

from app.components.painel_controle import (
    renderizar_bancada
)

# Configuração da página
st.set_page_config(
    page_title="HydroTwin - Painel de Controle", layout="wide", page_icon="🌱"
)

st.title("🌱 HydroTwin - Painel de Controle")

# ==========================================
# 🔐 Autenticação e Permissão
# ==========================================
usuario = get_current_user()
if usuario is None:
    st.error("❌ Você precisa estar autenticado para acessar esta página.")
    st.stop()

require_page_access(usuario, "Painel de Controle - Bancadas")

# Organização por Abas
tab_listar, tab_cadastrar = st.tabs(
    ["📋 Bancadas Cadastradas", "➕ Nova Bancada"]
)

# ==========================================
# TAB 1: LISTAR E GERENCIAR BANCADAS
# ==========================================
with tab_listar:
    st.header(
        "Bancadas por Controlador",
        help="Visualize e gerencie suas bancadas organizadas por cada controlador/Arduino.",
    )

    controladores = get_controladores() or []
    bancadas = get_bancadas() or []

    if not controladores:
        st.info("Nenhum controlador cadastrado até o momento.")
    else:
        # Dicionário de acesso rápido às bancadas por ID
        bancada_map = {b[0]: b for b in bancadas}
        bancadas_vinculadas_ids = set()

        # Agrupamento por Controlador
        for ctrl in controladores:
            ctrl_id, ctrl_name, b1_id, b2_id = ctrl

            # Filtra quais bancadas pertencem a este controlador
            bancadas_ctrl = []
            if b1_id and b1_id in bancada_map:
                bancadas_ctrl.append(bancada_map[b1_id])
                bancadas_vinculadas_ids.add(b1_id)
            if b2_id and b2_id in bancada_map:
                bancadas_ctrl.append(bancada_map[b2_id])
                bancadas_vinculadas_ids.add(b2_id)

            qtd_ocupada = len(bancadas_ctrl)

            # Cabeçalho do Controlador
            st.markdown(f"### 🎛️ Controlador: `{ctrl_name}`")
            st.caption(f"**Capacidade utilizada:** `{qtd_ocupada}/2` bancadas atreladas")

            if not bancadas_ctrl:
                st.info("ℹ️ Nenhuma bancada associada a este controlador.")
            else:
                for b in bancadas_ctrl:
                    renderizar_bancada(b)

            st.divider()

        # Exibe bancadas órfãs (caso existam bancadas sem nenhum controlador vinculado)
        bancadas_orfas = [b for b in bancadas if b[0] not in bancadas_vinculadas_ids]
        if bancadas_orfas:
            st.subheader("⚠️ Bancadas Sem Controlador Vinculado")
            for b in bancadas_orfas:
                renderizar_bancada(b)

# ==========================================
# TAB 2: CADASTRO DE NOVA BANCADA
# ==========================================
with tab_cadastrar:
    st.header(
        "Cadastrar Nova Bancada",
        help="Crie uma nova bancada e defina seu primeiro filete obrigatório.",
    )

    # --- 1. VERIFICAÇÃO DE VAGAS EM CONTROLADORES ---
    controladores_disponiveis = obter_controladores_com_vagas() or []

    if not controladores_disponiveis:
        st.warning(
            "⚠️ **Cadastro Bloqueado:** Não há controladores disponíveis ou "
            "todos os existentes já atingiram o limite máximo de 2 bancadas atreladas."
        )
        st.info("💡 Conecte um novo controlador para desbloquear mais bancadas.")
    else:
        # Prepara as opções para o Selectbox
        # Monta o dicionário mostrando o nome e quantas vagas restam
        ctrl_dict = {}
        for c in controladores_disponiveis:
            c_id, c_name, b1, b2 = c
            vagas = 2 - ([b1, b2].count(None) == 0) - (b1 is not None) - (b2 is not None)
            vagas_restantes = [b1, b2].count(None)
            label = f"{c_name} ({vagas_restantes} vaga(s) disponível(is))"
            ctrl_dict[label] = c_id

        opcoes_controlador = list(ctrl_dict.keys())

        st.info(
            "💡 **Instruções:** Para inicializar uma bancada no HydroTwin, você deve registrar "
            "o nome identificador, vincular a um controlador e definir o primeiro filete de cultivo."
        )

        culturas = get_culturas() or []
        cultura_dict = {c[1]: c[0] for c in culturas}
        opcoes_cultura = ["Selecione a cultura"] + list(cultura_dict.keys())

        # Formulário de cadastro
        with st.form("form_nova_bancada", clear_on_submit=True):
            st.subheader("1️⃣ Informações da Bancada & Controlador")
            
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                nome_bancada = st.text_input(
                    "Nome da Bancada",
                    placeholder="Ex: Bancada 01 - Setor Norte",
                    help="Nome identificador da estrutura.",
                )
            with col_b2:
                # Seleção do Arduino/Controlador disponível
                controlador_label = st.selectbox(
                    "Controlador / Arduino",
                    opcoes_controlador,
                    help="Selecione qual Arduino irá gerenciar esta bancada.",
                )

            st.subheader("2️⃣ Primeiro Filete (Obrigatório)")
            col_c1, col_c2 = st.columns(2)

            with col_c1:
                cultura_nome = st.selectbox(
                    "Cultura Inicial",
                    opcoes_cultura,
                    help="Selecione a planta cultivada neste filete inicial.",
                )

            with col_c2:
                data_inicio = st.date_input(
                    "Data de Plantio",
                    value=date.today(),
                    format="DD/MM/YYYY",
                    help="Data do plantio inicial.",
                )

            st.divider()
            col_sub, _ = st.columns([1, 2])
            with col_sub:
                submitted = st.form_submit_button(
                    "💾 Cadastrar Bancada", width='stretch', type="primary"
                )

        # Processamento após envio
        if submitted:
            if not nome_bancada or not nome_bancada.strip():
                st.error("❌ Informe um nome válido para a bancada.")
            elif cultura_nome == "Selecione a cultura":
                st.error("❌ Selecione uma cultura para o primeiro filete.")
            elif not data_inicio:
                st.error("❌ Informe uma data de plantio válida.")
            else:
                try:
                    cultura_id = cultura_dict[cultura_nome]
                    controlador_id = ctrl_dict[controlador_label]

                    # 1. Cria a bancada
                    bancada_id = inserir_bancada(nome_bancada.strip())

                    if bancada_id is None:
                        st.error("❌ Não foi possível criar a bancada no banco de dados.")
                    else:
                        # 2. Associa a bancada ao controlador selecionado
                        
                        associar_bancada_ao_controlador(controlador_id, bancada_id)

                        # 3. Cria o filete inicial
                        inserir_filete(
                            bancada_id,
                            cultura_id,
                            data_inicio.strftime("%Y-%m-%d"),
                        )

                        st.success(f"✅ Bancada '{nome_bancada}' criada e associada ao controlador com sucesso!")

                        # 4. Sincronização com os sensores
                        enviado = enfileirar_envio(bancada_id, cultura_id)

                        if enviado:
                            with st.status("Sincronizando com os sensores...", expanded=True) as status_box:
                                max_tentativas = 50
                                sincronizado = False

                                for _ in range(max_tentativas):
                                    res = obter_status_envio(bancada_id)
                                    status_envio = res.get("status")

                                    if status_envio == "sucesso":
                                        limpar_status_envio(bancada_id)
                                        status_box.update(
                                            label="✅ Sistema sincronizado com sucesso!",
                                            state="complete",
                                        )
                                        sincronizado = True
                                        break

                                    if status_envio == "erro":
                                        limpar_status_envio(bancada_id)
                                        status_box.update(
                                            label=f"❌ Erro na sincronização: {res.get('mensagem')}",
                                            state="error",
                                        )
                                        sincronizado = True
                                        break

                                    time.sleep(0.2)

                                if not sincronizado:
                                    limpar_status_envio(bancada_id)
                                    status_box.update(
                                        label="⚠️ Tempo de resposta do sensor excedido.",
                                        state="error",
                                    )

                        time.sleep(1)
                        st.rerun()

                except Exception as e:
                    st.error(f"❌ Ocorreu um erro ao processar o cadastro: {e}")
