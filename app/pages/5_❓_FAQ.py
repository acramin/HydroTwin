from __future__ import annotations

import streamlit as st

from hydrotwin import logger

logger.debug("5_❓_FAQ.py")

st.set_page_config(
    page_title="Central de Ajuda - HydroTwin",
    layout="wide",
    page_icon="❓",
)

st.title("❓ Central de Ajuda — HydroTwin")
st.caption(
    "Entenda o monitoramento, os indicadores operacionais, a automação embarcada "
    "e os recursos disponíveis na plataforma."
)

with st.container(border=True):
    st.markdown(
        """
        O **HydroTwin** é uma aplicação local para monitoramento e automação de
        bancadas hidropônicas NFT. O Arduino Mega lê os sensores e controla alguns
        atuadores; o Raspberry Pi recebe as leituras, armazena os dados em SQLite
        e executa a aplicação Streamlit.
        """
    )
    c1, c2, c3 = st.columns(3)
    c1.metric("Armazenamento", "SQLite", "Banco local")
    c2.metric("Análise operacional", "pH + EC", "Status consolidado")
    c3.metric("Análises complementares", "Anomalias e tendências", "Séries de leituras")

st.divider()

st.subheader("🟢🟡🔴 Como interpretar o status operacional?")
st.markdown(
    """
    O status operacional consolidado implementado no processamento é calculado
    a partir das médias de **pH e EC** da janela analisada e dos limites disponíveis
    para a bancada/cultura. Para cada variável, a faixa de atenção é derivada da
    faixa ideal, com uma margem de 20% da amplitude entre os limites.
    """
)
col1, col2, col3 = st.columns(3)
with col1:
    st.success("**🟢 Saudável**")
    st.caption("Os valores avaliados estão dentro da faixa ideal configurada.")
with col2:
    st.warning("**🟡 Atenção**")
    st.caption("Um valor está fora da faixa ideal, mas ainda dentro da faixa de atenção.")
with col3:
    st.error("**🔴 Crítico**")
    st.caption("Um valor ultrapassou também a faixa de atenção configurada.")

st.info(
    "O status consolidado atualmente representa o estado operacional baseado em pH e EC. "
    "Anomalias e tendências são calculadas separadamente e armazenadas como indicadores "
    "complementares; não são combinadas automaticamente ao status consolidado."
)

st.divider()
st.subheader("📚 Perguntas frequentes")

tab_inicio, tab_dados, tab_analise, tab_controle = st.tabs(
    [
        "🚀 Primeiros passos",
        "📡 Sensores e dados",
        "📊 Indicadores e alertas",
        "🔧 Automação e acesso",
    ]
)

with tab_inicio:
    with st.expander("O que é o HydroTwin?"):
        st.markdown(
            """
            É um sistema acadêmico de monitoramento e automação para cultivo hidropônico
            NFT. A solução combina firmware no Arduino Mega com uma aplicação Python
            executada localmente no Raspberry Pi. A interface é feita em Streamlit e
            os dados são armazenados em SQLite.
            """
        )

    with st.expander("O HydroTwin é um gêmeo digital ou usa inteligência artificial?"):
        st.markdown(
            """
            A implementação atual deve ser descrita como um **sistema de monitoramento
            e automação com análise de dados**. O código de processamento utiliza limites
            operacionais, estatísticas, comparação com médias recentes e cálculo simples
            de tendências. Não há, nas rotinas analisadas, um modelo de simulação física
            do cultivo ou um modelo de inteligência artificial para previsão de crescimento.
            """
        )

    with st.expander("Como cadastro uma bancada?"):
        st.markdown(
            """
            1. Entre na plataforma com uma conta autorizada.
            2. Abra **Painel de Controle – Bancadas**.
            3. Acesse a aba de nova bancada, informe os dados solicitados e selecione a cultura.
            4. Associe a bancada a um controlador disponível e informe os dados do primeiro filete.
            5. Salve o cadastro.

            A interface limita o vínculo a até duas bancadas por controlador. As opções
            disponíveis podem depender dos controladores já cadastrados.
            """
        )

    with st.expander("Qual é a diferença entre bancada e filete?"):
        st.markdown(
            """
            A **bancada** é a unidade usada para associar o controlador e organizar as
            leituras dos sensores. O **filete** representa uma parte do cultivo que pode
            ter seus próprios dados de plantio e cultura. As leituras do firmware são
            identificadas por bancada, não por filete individual.
            """
        )

with tab_dados:
    with st.expander("Quais variáveis são monitoradas?"):
        st.markdown(
            """
            O protocolo de telemetria da aplicação recebe:
            - pH;
            - condutividade elétrica (EC);
            - temperatura ambiente;
            - umidade do ar;
            - temperatura da água;
            - luminosidade;
            - estado da boia de nível do tanque.

            A disponibilidade e a qualidade dos valores dependem dos sensores, da
            calibração e da comunicação com o hardware.
            """
        )

    with st.expander("Com que frequência chegam os dados?"):
        st.markdown(
            """
            O firmware incluído no snapshot transmite as leituras das duas bancadas
            em intervalos de aproximadamente **10 segundos**. No Raspberry Pi, o
            processamento periódico está configurado para rodar a cada **1 hora**,
            quando há bancadas com novas leituras pendentes. O intervalo de aquisição
            e o intervalo de processamento são coisas diferentes.
            """
        )

    with st.expander("Onde os dados são armazenados?"):
        st.markdown(
            """
            A aplicação usa **SQLite**, um banco de dados local. As leituras recebidas
            são registradas como dados brutos e, durante o processamento, são calculadas
            estatísticas e indicadores que também são armazenados no banco.
            """
        )

    with st.expander("O sistema precisa de internet?"):
        st.markdown(
            """
            A arquitetura da aplicação é local: o backend utiliza SQLite e a interface
            é servida pelo Streamlit no ambiente em que o sistema está instalado. O
            monitoramento local não exige um serviço de banco de dados em nuvem. Acesso
            remoto, notificações externas ou outros serviços conectados não devem ser
            considerados garantidos pela implementação descrita aqui.
            """
        )

    with st.expander("Por que aparece 'Sem dados' ou faltam gráficos/análises?"):
        st.markdown(
            """
            Pode não haver leituras registradas para a bancada ou ainda não existir
            quantidade suficiente de amostras para uma análise específica. A detecção
            de anomalias usa uma janela de 30 leituras e a análise de tendências precisa
            de pelo menos 60 leituras válidas por variável. Verifique também se o
            controlador está conectado e se as mensagens estão sendo recebidas.
            """
        )

with tab_analise:
    with st.expander("Como o status operacional é calculado?"):
        st.markdown(
            """
            O processamento obtém as médias de pH e EC na janela consultada e compara
            esses valores com os limites operacionais da bancada/cultura. O status geral
            é o mais severo entre os sensores avaliados: **Saudável**, **Atenção** ou
            **Crítico**. Se não houver valores utilizáveis, o resultado pode ser
            **Sem dados**.
            """
        )

    with st.expander("O que é uma anomalia?"):
        st.markdown(
            """
            A rotina compara o valor mais recente com a média das leituras anteriores
            dentro de uma janela de até 30 amostras. Desvios percentuais de até 10% são
            classificados como saudáveis; acima de 10% e até 20%, como atenção; acima
            de 20%, como críticos. A rotina ignora a variável categórica de nível do tanque.
            """
        )

    with st.expander("Como a tendência é calculada?"):
        st.markdown(
            """
            A rotina compara a média de uma janela de 30 amostras com a média das
            30 amostras anteriores. Variações absolutas inferiores a 5% são consideradas
            estáveis; variações de 5% a menos de 20% são classificadas como subida ou
            descida; variações de 20% ou mais são consideradas mudança brusca. A direção
            da variação, por si só, não significa necessariamente melhora ou piora agronômica.
            """
        )

    with st.expander("O sistema cria alertas?"):
        st.markdown(
            """
            O backend sincroniza alertas de risco operacional quando o estado calculado
            a partir de pH e EC indica atenção ou criticidade. As análises de anomalia e
            tendência são registradas separadamente. O sistema não deve ser descrito
            como prevendo falhas ou garantindo a saúde das plantas.
            """
        )

    with st.expander("Todos os sensores influenciam o status consolidado?"):
        st.markdown(
            """
            Não. Embora as estatísticas, as anomalias e as tendências considerem outras
            variáveis, o status operacional consolidado implementado em `processar_sensor`
            é calculado com **pH e EC**. A boia, a temperatura, a umidade e a luminosidade
            aparecem como dados monitorados e podem participar de análises complementares,
            mas não entram nesse status consolidado atual.
            """
        )

with tab_controle:
    with st.expander("O que o Arduino controla automaticamente?"):
        st.markdown(
            """
            No firmware analisado, o Arduino controla:
            - **Iluminação dimerizável:** ajusta o PWM entre intensidade total e reduzida
              quando a leitura de luminosidade atinge o dobro do limite máximo recebido;
            - **Iluminação com temporização:** executa um ciclo de 16 horas ligada e
              8 horas desligada após a configuração da bancada;
            - **Bombas de nutrientes:** calcula um tempo de acionamento com base na
              diferença entre a EC medida e o limite mínimo recebido, com um limite
              máximo de 5 segundos por acionamento.

            O comportamento real depende da configuração, da calibração dos sensores,
            da instalação elétrica/hidráulica e dos atuadores conectados.
            """
        )

    with st.expander("O HydroTwin corrige o pH automaticamente?"):
        st.markdown(
            """
            **Não, não na implementação analisada.** O firmware recebe os limites de
            pH, mas a rotina de atuação das bombas de nutrientes utiliza a EC para
            calcular o acionamento. Não há uma rotina equivalente de dosagem de corretor
            de pH demonstrada nesse código.
            """
        )

    with st.expander("O sistema controla automaticamente a vazão ou o nível da água?"):
        st.markdown(
            """
            A telemetria recebida pela aplicação inclui o estado da boia do tanque,
            mas o firmware analisado não apresenta uma rotina de controle automático
            de vazão ou de reposição de água com base nessa leitura. Não confunda
            monitorar uma variável com atuar automaticamente sobre ela.
            """
        )

    with st.expander("Como funciona a comunicação com o Arduino?"):
        st.markdown(
            """
            O Raspberry Pi recebe linhas de telemetria identificadas como `B1:` e `B2:`.
            Também pode enviar mensagens `PARAMS` com identificadores e parâmetros da
            cultura. O firmware responde com `PARAMS_OK` quando aceita a configuração
            ou `PARAMS_ERROR` quando há erro. O backend mantém uma fila de envio e
            acompanha a confirmação recebida.
            """
        )

    with st.expander("Quais são os perfis de acesso?"):
        st.markdown(
            """
            A aplicação utiliza os perfis **admin** e **viewer**. O administrador tem
            permissões de gerenciamento que não estão disponíveis ao visualizador.
            O acesso efetivo a cada página depende das regras de autorização configuradas
            no sistema.
            """
        )

    with st.expander("Para que serve o simulador?"):
        st.markdown(
            """
            O simulador gera leituras sintéticas para exercitar o processamento e a
            interface sem depender continuamente do hardware físico. Na implementação
            atual, a página é restrita ao ambiente de desenvolvimento e a usuários com
            perfil de administrador. Dados simulados não são medições reais do cultivo.
            """
        )

st.divider()
st.subheader("🔗 Documentação e código-fonte")
st.markdown(
    """
    Para consultar a implementação e a documentação técnica, acesse o
    [repositório HydroTwin no GitHub](https://github.com/acramin/HydroTwin).
    """
)
