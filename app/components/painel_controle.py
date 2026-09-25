from __future__ import annotations

from datetime import date
import streamlit as st

from hydrotwin import (
    formatar_data_filete,
    get_culturas,
    get_filetes_by_bancada,
    inserir_filete,
    update_bancada_concluido,
    update_filete_colhido,
    logger
)

def renderizar_bancada(bancada):
    logger.debug("renderizar_bancada(bancada)")
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
                with st.popover("➕ Novo Filete", width='stretch'):
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
                                width='stretch',
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
