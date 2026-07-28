from __future__ import annotations

from datetime import date
import time
import streamlit as st

from hydrotwin import (
    enfileirar_envio,
    formatar_data_filete,
    get_bancadas,
    get_culturas,
    get_current_user,
    get_filetes_by_bancada,
    inserir_bancada,
    inserir_filete,
    limpar_status_envio,
    obter_status_envio,
    require_page_access,
    update_bancada_concluido,
    update_filete_colhido,
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
        "Bancadas Cadastradas",
        help="Visualize e gerencie suas bancadas e filetes de cultivo.",
    )

    bancadas = get_bancadas() or []

    if not bancadas:
        st.info(
            "Nenhuma bancada cadastrada ainda. Crie uma nova bancada na aba ao lado para começar!"
        )
    else:
        # Ordenar bancadas por ID
        bancadas_ordenadas = sorted(bancadas, key=lambda x: x[0])

        for bancada in bancadas_ordenadas:
            (
                bancada_id,
                nome_bancada,
                _cultura_nome,
                _filete_id,
                _data_plantio,
                _data_colheita,
                flag_concluido,
            ) = bancada

            status_tag = "✅ Concluída" if flag_concluido else "🟢 Em Andamento"
            titulo_expander = f"🌿 {nome_bancada} — [{status_tag}]"

            with st.expander(titulo_expander, expanded=not flag_concluido):
                col_header, col_actions = st.columns([3, 1])

                with col_header:
                    st.caption(f"**ID da Bancada:** `{bancada_id}`")

                # Botão em Popover para Adicionar Filete
                with col_actions:
                    if not flag_concluido:
                        with st.popover("➕ Novo Filete", use_container_width=True):
                            st.markdown(f"**Adicionar Filete na bancada: {nome_bancada}**")
                            culturas = get_culturas() or []
                            cultura_dict = {c[1]: c[0] for c in culturas}
                            opcoes_cultura = ["Selecione a cultura"] + list(cultura_dict.keys())

                            nova_cultura = st.selectbox(
                                "Cultura",
                                opcoes_cultura,
                                key=f"pop_cultura_{bancada_id}",
                            )
                            nova_data = st.date_input(
                                "Data de Plantio",
                                value=date.today(),
                                format="DD/MM/YYYY",
                                key=f"pop_data_{bancada_id}",
                            )

                            if st.button("Confirmar Adição", key=f"pop_btn_{bancada_id}", type="primary"):
                                if nova_cultura == "Selecione a cultura":
                                    st.error("Selecione uma cultura válida.")
                                else:
                                    try:
                                        c_id = cultura_dict[nova_cultura]
                                        inserir_filete(
                                            bancada_id,
                                            c_id,
                                            nova_data.strftime("%Y-%m-%d"),
                                        )
                                        # Atualiza estado da bancada
                                        update_bancada_concluido(bancada_id, 0)
                                        st.success("Filete adicionado com sucesso!")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Erro ao criar filete: {e}")

                st.divider()

                # Listagem de Filetes
                filetes = get_filetes_by_bancada(bancada_id) or []

                if not filetes:
                    st.warning("Nenhum filete cadastrado nesta bancada.")
                else:
                    filetes_ordenados = sorted(filetes, key=lambda x: x[0])
                    todos_colhidos = True

                    st.markdown("**Filetes de Cultivo:**")

                    for f in filetes_ordenados:
                        (
                            f_id,
                            _,
                            _,
                            cultura_nome_f,
                            data_plant,
                            prev_colh,
                            flag_colhido,
                            data_colh,
                        ) = f

                        if not flag_colhido:
                            todos_colhidos = False

                        with st.container(border=True):
                            f_col1, f_col2, f_col3, f_col4, f_col5 = st.columns(
                                [1.5, 2.5, 2, 2, 2.5]
                            )

                            f_col1.markdown(f"**Filete #{f_id}**")
                            f_col2.write(f"🌱 {cultura_nome_f or 'N/A'}")
                            f_col3.write(f"📅 Plantio: {formatar_data_filete(data_plant)}")
                            f_col4.write(f"🎯 Previsão: {formatar_data_filete(prev_colh)}")

                            with f_col5:
                                if not flag_colhido:
                                    if st.button(
                                        "🌾 Marcar Colhido",
                                        key=f"btn_colher_{f_id}",
                                        use_container_width=True,
                                    ):
                                        update_filete_colhido(f_id, 1)

                                        # Verifica se a bancada deve ser marcada como concluída
                                        filetes_at = get_filetes_by_bancada(bancada_id)
                                        if all(item[6] for item in filetes_at):
                                            update_bancada_concluido(bancada_id, 1)

                                        st.rerun()
                                else:
                                    st.success(
                                        f"Colhido em: {formatar_data_filete(data_colh)}"
                                    )

                    # Sincronização do status da bancada se necessário
                    if filetes and todos_colhidos != bool(flag_concluido):
                        update_bancada_concluido(bancada_id, 1 if todos_colhidos else 0)


# ==========================================
# TAB 2: CADASTRO DE NOVA BANCADA
# ==========================================
with tab_cadastrar:
    st.header(
        "Cadastrar Nova Bancada",
        help="Crie uma nova bancada e defina seu primeiro filete obrigatório.",
    )

    st.info(
        "💡 **Instruções:** Para inicializar uma bancada no HydroTwin, você deve registrar "
        "o nome identificador e o primeiro filete de cultivo."
    )

    culturas = get_culturas() or []
    cultura_dict = {c[1]: c[0] for c in culturas}
    opcoes_cultura = ["Selecione a cultura"] + list(cultura_dict.keys())

    # Formulário simplificado e limpo
    with st.form("form_nova_bancada", clear_on_submit=True):
        st.subheader("1️⃣ Informações da Bancada")
        nome_bancada = st.text_input(
            "Nome da Bancada",
            placeholder="Ex: Bancada 01 - Setor Norte",
            help="Nome identificador da estrutura.",
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
                "💾 Cadastrar Bancada", use_container_width=True, type="primary"
            )

    # Processamento após o envio do formulário
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
                bancada_id = inserir_bancada(nome_bancada.strip())

                if bancada_id is None:
                    st.error("❌ Não foi possível criar a bancada no banco de dados.")
                else:
                    inserir_filete(
                        bancada_id,
                        cultura_id,
                        data_inicio.strftime("%Y-%m-%d"),
                    )

                    st.success(f"✅ Bancada '{nome_bancada}' criada com sucesso!")

                    # Processamento visual do enfileiramento do sistema
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