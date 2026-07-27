import streamlit as st

st.set_page_config(page_title="Hydroponic Monitor", layout="wide", page_icon="🌱")

st.title("❓ FAQ")
st.caption("Resumo das funcionalidades do HydroTwin e guia rápido de interpretação das informações exibidas nas demais páginas.")

st.markdown(
	"""
	O HydroTwin foi pensado para centralizar o cadastro, o acompanhamento e a leitura operacional de bancadas hidropônicas.
	A plataforma organiza os dados coletados pelos sensores, calcula indicadores consolidados e destaca alertas, anomalias e tendências
	para facilitar a tomada de decisão.

	O acesso é controlado por login: novos usuários são cadastrados como `viewer` e o usuário `admin` com role `admin` é o único que pode cadastrar bancadas.
	"""
)

col1, col2, col3 = st.columns(3)
col1.metric("Páginas principais", "4")
col2.metric("Status possíveis", "3")
col3.metric("Nível de leitura", "Resumo + detalhe")

st.subheader("O que o sistema faz")
st.markdown(
	"""
	- **Cadastra bancadas e culturas** para vincular cada área de cultivo ao seu contexto.
	- **Recebe leituras dos sensores** e grava os dados brutos no banco.
	- **Processa os dados automaticamente** para gerar status, score e histórico.
	- **Detecta alertas, anomalias e tendência operacional** para sinalizar riscos e mudanças no comportamento da bancada.
	- **Exibe uma visão geral e uma visão detalhada** para apoiar a leitura rápida e a análise técnica.
	"""
)

st.subheader("Como interpretar os status")
st.markdown(
	"""
	- **Saudável**: os indicadores estão dentro do esperado para a janela analisada.
	- **Atenção**: algum sensor ou métrica começou a se aproximar de limites sensíveis.
	- **Crítico**: há forte indício de condição fora do padrão ou de risco operacional elevado.

	Na página de monitoramento detalhado, o **status consolidado** combina risco atual, anomalia e tendência operacional.
	Isso reduz ambiguidades quando um indicador aponta normalidade e outro aponta risco.
	"""
)

st.subheader("Perguntas rápidas")

with st.expander("Como cadastrar uma bancada?"):
	st.write(
		"Na página **Cadastrar Bancada**, informe o nome da bancada, selecione a cultura e defina a data de início. "
		"Se a bancada já existir, escolha-a e adicione mais filetes."
	)

with st.expander("O que vejo na página Visão Geral?"):
	st.markdown(
		"""
		A página **Visão Geral** mostra três blocos principais:

		- **Status das bancadas**: resumo rápido do estado atual de cada bancada.
		- **Indicadores gerais**: KPIs derivados da última leitura processada, como nível do tanque, pH, EC,
		  umidade, temperatura e vazão.
		- **Alertas ativos**: mensagens das condições que ainda exigem atenção.
		"""
	)
	st.info(
		"Se não houver leitura processada ainda, o sistema exibirá mensagens de orientação para indicar que os dados brutos "
		"ainda não foram suficientes para gerar KPIs ou status."
	)

with st.expander("Como interpretar os indicadores da Visão Geral?"):
	st.markdown(
		"""
		- **Status da bancada**: representa a leitura mais recente consolidada para cada bancada.
		- **Nível do tanque**: aparece como **OK** quando a leitura está acima do limiar interno e como **Baixo** quando está abaixo.
		- **pH e EC**: indicam se a solução nutritiva está dentro da faixa esperada da cultura cadastrada.
		- **Umidade, temperatura e vazão**: ajudam a avaliar o ambiente e a circulação da água.
		- **Alertas ativos**: indicam situações que ainda não foram resolvidas no banco.
		"""
	)

with st.expander("O que muda no Monitoramento Detalhado?"):
	st.markdown(
		"""
		A página **Monitoramento Detalhado** aprofunda a análise de uma bancada específica.

		- **Status consolidado**: leitura unificada do estado da bancada.
		- **Score consolidado**: severidade agregada entre risco, anomalia e tendência.
		- **Score de risco**: reflete o risco estatístico da janela processada.
		- **Gráficos por variável**: mostram a evolução das métricas com opção de visualização por **Zona** ou por **Linha**.
		- **Contribuição do risco**: ajuda a entender quais sensores mais pesaram no estado atual.
		- **Anomalias**: destacam medições fora do padrão esperado.
		- **Tendência operacional**: indica se a bancada está melhorando, piorando ou se mantendo estável.
		- **Leituras recentes**: exibem os dados brutos mais novos para conferência.
		"""
	)

with st.expander("Como interpretar os gráficos por variável?"):
	st.markdown(
		"""
		- **Modo Zona**: sobrepõe faixas de risco para facilitar a leitura de valores fora do esperado.
		- **Modo Linha**: mostra apenas a evolução temporal, útil para observar tendência.
		- **Faixas coloridas**: ajudam a perceber rapidamente quando uma variável entra em atenção ou em criticidade.
		"""
	)

with st.expander("O que significam anomalia e tendência operacional?"):
	st.markdown(
		"""
		- **Anomalia** identifica comportamentos estatisticamente incomuns na janela recente.
		- **Tendência operacional** resume a direção do comportamento recente, considerando consistência, força e estabilidade.
		- **Score mais alto** significa maior severidade ou maior confiança de que a mudança merece atenção.
		"""
	)

with st.expander("Como usar a simulação?"):
	st.write(
		"Na tela inicial, a simulação gera leituras falsas em intervalos curtos para testar o fluxo de cadastro, processamento, "
		"visualização e alertas sem depender de sensores físicos."
	)

st.subheader("Perguntas frequentes")

st.markdown(
	"""
	**Por que a Visão Geral e o Monitoramento Detalhado podem mostrar diferenças?**

	A Visão Geral prioriza um resumo rápido da última leitura consolidada. Já o Monitoramento Detalhado analisa uma bancada isoladamente,
	com mais contexto de janela, tendência, anomalia e séries históricas.

	**Por que posso ver "Sem dados"?**

	Isso acontece quando ainda não houve leituras suficientes para processar a bancada ou quando o cadastro existe, mas os dados de sensores
	ainda não foram recebidos.

	**Os alertas somem automaticamente?**

	Eles são resolvidos quando o estado volta a ficar saudável e o processamento consolida essa mudança.
	"""
)

st.info(
	"Para mais informações e documentação do projeto acesse o repositório oficial: [HydroTwin Documentation](https://github.com/acramin/hydrotwin)"
)
