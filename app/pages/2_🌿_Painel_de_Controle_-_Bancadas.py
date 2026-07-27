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

st.set_page_config(page_title="Hydroponic Monitor", layout="wide")

st.title("🌱 HydroTwin - Painel de Controle")

# Verificar autenticação e acesso
usuario = get_current_user()
if usuario is None:
    st.error("❌ Você precisa estar autenticado para acessar esta página.")
    st.stop()

require_page_access(usuario, "Painel de Controle - Bancadas")

# Separar em abas
tab1, tab2 = st.tabs(["📋 Bancadas Cadastradas", "➕ Nova Bancada"])

# =========================
# TAB 1: LISTAR BANCADAS
# =========================
with tab1:
    st.header(
        "Bancadas Cadastradas", help="Visualize e gerencie suas bancadas e filetes"
    )

    bancadas = get_bancadas()

    if not bancadas:
        st.info(
            "Nenhuma bancada cadastrada ainda. Crie uma nova bancada para começar!"
        )
    else:
        bancadas.sort(key=lambda x: x[0])  # Ordenar por ID da bancada
        for (
            bancada_id,
            nome_bancada,
            cultura_nome,
            filete_id,
            data_plantio,
            data_colheita,
            flag_concluido,
        ) in bancadas:
            with st.expander(
                f"🌿 {nome_bancada} | {'Concluída' if flag_concluido else 'Em andamento'}",
                expanded=False,
            ):
                if flag_concluido:
                    col1, col2 = st.columns([4, 0.1])
                else:
                    col1, col2 = st.columns([3, 0.60])

                with col1:
                    st.markdown(f"**ID da Bancada:** {bancada_id}")

                    # Mostrar filetes dessa bancada
                    filetes = get_filetes_by_bancada(bancada_id)

                    st.markdown("**Filetes Ativas:**")
                    if filetes:
                        filetes.sort(
                            key=lambda x: x[0]
                        )  # Ordenar por ID do filete
                        if flag_concluido:
                            st.success(
                                "✅ Esta bancada está concluída! Todos os filetes foram colhidos."
                            )

                        # Processar cada filete
                        for (
                            f_id,
                            f_bancada_id,
                            cultura_id,
                            cultura_nome_f,
                            data_plant,
                            prev_colh,
                            flag_colhido,
                            data_colh,
                        ) in filetes:
                            col_f1, col_f2, col_f3, col_f4, col_f5 = st.columns(
                                [2, 2, 2, 3, 2]
                            )
                            with col_f1:
                                st.caption(f"**Filete #{f_id}**")
                            with col_f2:
                                st.caption(
                                    f"Cultura: {cultura_nome_f or 'N/A'}"
                                )
                            with col_f3:
                                st.caption(
                                    f"Plantio: {formatar_data_filete(data_plant)}"
                                )
                            with col_f4:
                                st.caption(
                                    f"Previsão Colheita: {formatar_data_filete(prev_colh)}"
                                )
                            with col_f5:
                                if not flag_colhido:
                                    select_box = st.selectbox(
                                        "Colhido?",
                                        ["Não", "Sim"],
                                        key=f"sel_filete_{f_id}",
                                        index=0,
                                        help="Marque este filete como colhido quando for o caso",
                                    )
                                    if select_box == "Sim" and not flag_colhido:
                                        update_filete_colhido(f_id, 1)
                                        st.rerun()
                                else:
                                    st.caption(
                                        f"Coletado em {formatar_data_filete(data_colh)}"
                                    )

                        filetes_atualizados = get_filetes_by_bancada(bancada_id)
                        todos_coletados = all(
                            f[6] for f in filetes_atualizados
                        )

                        if todos_coletados:
                            update_bancada_concluido(bancada_id, 1)
                        else:
                            update_bancada_concluido(bancada_id, 0)
                    else:
                        st.caption("Nenhum filete cadastrado")

                with col2:
                    if not flag_concluido:
                        if st.button(
                            "➕ Adicionar Filete",
                            key=f"btn_add_filete_{bancada_id}",
                        ):
                            st.session_state[
                                f"show_form_filete_{bancada_id}"
                            ] = True

                # Formulário para adicionar filete (se clicado)
                if st.session_state.get(f"show_form_filete_{bancada_id}"):
                    st.markdown("---")
                    st.markdown("**Adicionar Novo Filete a esta Bancada**")

                    culturas = get_culturas()
                    cultura_dict = {c[1]: c[0] for c in culturas}
                    opcoes_cultura = ["Selecione a cultura"] + list(
                        cultura_dict.keys()
                    )

                    col_f1, col_f2 = st.columns(2)

                    with col_f1:
                        cultura_nome_novo = st.selectbox(
                            "Cultura",
                            opcoes_cultura,
                            index=0,
                            key=f"sel_cultura_filete_{bancada_id}",
                        )

                    with col_f2:
                        data_plantio_novo = st.date_input(
                            "Data de Plantio",
                            value=date.today(),
                            format="DD/MM/YYYY",
                            key=f"inp_data_filete_{bancada_id}",
                        )

                    col_btn1, col_btn2 = st.columns(2)

                    with col_btn1:
                        if st.button(
                            "✅ Confirmar",
                            key=f"btn_confirmar_filete_{bancada_id}",
                        ):
                            if cultura_nome_novo == "Selecione a cultura":
                                st.error(
                                    "Selecione uma cultura antes de confirmar."
                                )
                            else:
                                cultura_id = cultura_dict[cultura_nome_novo]
                                try:
                                    inserir_filete(
                                        bancada_id,
                                        cultura_id,
                                        data_plantio_novo.strftime("%Y-%m-%d"),
                                    )
                                    st.success(
                                        f"✅ Filete criado com sucesso! Cultura: {cultura_nome_novo}"
                                    )
                                    st.session_state[
                                        f"show_form_filete_{bancada_id}"
                                    ] = False
                                    st.rerun()
                                except Exception as e:
                                    st.error(
                                        f"Erro ao criar filete: {str(e)}"
                                    )

                    with col_btn2:
                        if st.button(
                            "❌ Cancelar",
                            key=f"btn_cancelar_filete_{bancada_id}",
                        ):
                            st.session_state[
                                f"show_form_filete_{bancada_id}"
                            ] = False
                            st.rerun()


# =========================
# TAB 2: CRIAR NOVA BANCADA
# =========================
with tab2:
    if "salvando_bancada" not in st.session_state:
        st.session_state.salvando_bancada = False
    if "nova_bancada_pendente" not in st.session_state:
        st.session_state.nova_bancada_pendente = None
    if "reset_form" not in st.session_state:
        st.session_state.reset_form = False
    if "nome_bancada_nova" not in st.session_state:
        st.session_state.nome_bancada_nova = ""
    if "cultura_primeira_bancada" not in st.session_state:
        st.session_state.cultura_primeira_bancada = "Selecione a cultura"
    if "data_primeira_bancada" not in st.session_state:
        st.session_state.data_primeira_bancada = date.today()

    if st.session_state.reset_form:
        st.session_state.nome_bancada_nova = ""
        st.session_state.cultura_primeira_bancada = "Selecione a cultura"
        st.session_state.data_primeira_bancada = date.today()
        st.session_state.reset_form = False

    def iniciar_salvamento_bancada():
        st.session_state.nova_bancada_pendente = {
            "nome_bancada": st.session_state.nome_bancada_nova,
            "cultura_nome": st.session_state.cultura_primeira_bancada,
            "data_inicio": st.session_state.data_primeira_bancada,
        }
        st.session_state.salvando_bancada = True

    st.header(
        "Cadastrar Nova Bancada",
        help="Crie uma nova bancada com seu primeiro filete",
    )

    st.markdown("""
    Para criar uma nova bancada, você precisa:
    1. **Nome da Bancada** - identificar sua bancada
    2. **Primeiro Filete** - cultura e data de plantio (obrigatório)
    3. **Filetes Adicionais** - podem ser adicionados depois
    """)

    st.markdown("---")

    bancada_em_salvamento = st.session_state.salvando_bancada

    with st.form("form_nova_bancada"):
        # Seção 1: Dados da Bancada
        st.subheader("1️⃣ Informações da Bancada")
        nome_bancada = st.text_input(
            "Nome da Bancada",
            key="nome_bancada_nova",
            help="Ex: Bancada 1, Setor A, etc.",
            disabled=bancada_em_salvamento,
        )

        # Seção 2: Primeiro Filete (obrigatório)
        st.subheader("2️⃣ Primeiro Filete (Obrigatório)")

        culturas = get_culturas()
        cultura_dict = {c[1]: c[0] for c in culturas}
        opcoes_cultura = ["Selecione a cultura"] + list(cultura_dict.keys())

        col1, col2 = st.columns(2)

        with col1:
            cultura_nome = st.selectbox(
                "Cultura",
                opcoes_cultura,
                key="cultura_primeira_bancada",
                help="Selecione a cultura para o primeiro filete",
                disabled=bancada_em_salvamento,
            )

        with col2:
            # CORRIGIDO: Removido o 'value' pois a chave no session_state já gerencia o valor
            data_inicio = st.date_input(
                "Data de Plantio",
                format="DD/MM/YYYY",
                key="data_primeira_bancada",
                help="Data de início do cultivo",
                disabled=bancada_em_salvamento,
            )

        col_submit, col_empty = st.columns([1, 4])

        with col_submit:
            submitted = st.form_submit_button(
                "💾 Cadastrar Bancada",
                use_container_width=True,
                disabled=bancada_em_salvamento,
                on_click=iniciar_salvamento_bancada,
            )

    if st.session_state.salvando_bancada and st.session_state.nova_bancada_pendente:
        dados_bancada = st.session_state.nova_bancada_pendente
        nome_bancada = dados_bancada["nome_bancada"]
        cultura_nome = dados_bancada["cultura_nome"]
        data_inicio = dados_bancada["data_inicio"]

        # Validações antes de prosseguir
        if not nome_bancada or nome_bancada.strip() == "":
            st.error("❌ Digite um nome para a bancada.")
            st.session_state.salvando_bancada = False
            st.session_state.nova_bancada_pendente = None
            st.stop()

        if cultura_nome == "Selecione a cultura":
            st.error("❌ Selecione uma cultura para o primeiro filete.")
            st.session_state.salvando_bancada = False
            st.session_state.nova_bancada_pendente = None
            st.stop()

        if not data_inicio:
            st.error("❌ Selecione uma data de plantio.")
            st.session_state.salvando_bancada = False
            st.session_state.nova_bancada_pendente = None
            st.stop()

        try:
            cultura_id = cultura_dict[cultura_nome]
            bancada_id = inserir_bancada(nome_bancada)

            if bancada_id is None:
                st.error("❌ Erro ao criar a bancada. Tente novamente.")
                st.session_state.salvando_bancada = False
                st.session_state.nova_bancada_pendente = None
                st.stop()

            inserir_filete(
                bancada_id, cultura_id, data_inicio.strftime("%Y-%m-%d")
            )

            st.success(f"✅ Bancada '{nome_bancada}' cadastrada com sucesso!")

            enviado = enfileirar_envio(bancada_id, cultura_id)

            if enviado:
                with st.spinner("Atualizando sistema..."):
                    max_tentativas = 50

                    for _ in range(max_tentativas):
                        status = obter_status_envio(bancada_id)

                        if status["status"] == "sucesso":
                            limpar_status_envio(bancada_id)
                            st.success("✅ Sistema atualizado.")
                            break

                        if status["status"] == "erro":
                            limpar_status_envio(bancada_id)
                            st.error(status["mensagem"])
                            break

                        time.sleep(0.2)
                    else:
                        limpar_status_envio(bancada_id)
                        st.warning("Tempo de espera excedido.")

            st.session_state.reset_form = True

        except Exception as e:
            st.error(f"❌ Erro ao cadastrar bancada: {str(e)}")

        finally:
            st.session_state.salvando_bancada = False
            st.session_state.nova_bancada_pendente = None
            st.rerun()