# Interface e guia de uso

Este documento descreve as páginas e os principais fluxos disponíveis na interface do HydroTwin, com foco em quem utiliza a aplicação. A interface foi construída com Streamlit e reúne consulta de leituras, indicadores operacionais, gerenciamento das bancadas e ferramentas administrativas.

A disponibilidade de algumas páginas e ações depende do perfil autenticado e do ambiente em que a aplicação está executando. Os nomes e comportamentos descritos aqui correspondem ao snapshot da interface usado como referência para esta documentação.

## Visão geral da navegação

| Página | Para que serve |
|---|---|
| **HydroTwin** | Apresenta o projeto e permite entrar ou criar uma conta usando um convite. |
| **Painel de Controle – Bancadas** | Cadastra e organiza bancadas, associa controladores e acompanha os filetes de cultivo. |
| **Visão Geral** | Mostra um resumo do estado operacional, indicadores recentes e alertas ativos. |
| **Monitoramento Detalhado** | Permite selecionar uma bancada e consultar gráficos, análises e leituras recebidas. |
| **Central de Ajuda (FAQ)** | Explica conceitos, indicadores, limites e dúvidas comuns de uso. |
| **Simulador de Leituras** | Gera dados fictícios para exercitar a visualização durante o desenvolvimento. |
| **Controle de Acesso** | Lista usuários e permite enviar convites com um perfil de acesso. |

## 1. Página inicial — HydroTwin

A página inicial apresenta o propósito do sistema, o funcionamento geral do monitoramento hidropônico NFT e as variáveis acompanhadas. Também explica, em linguagem introdutória, a divisão entre aquisição dos dados, supervisão e atuação embarcada.

### Entrar

Na aba **Entrar**, a pessoa informa o nome de usuário e a senha. Se os dados não forem aceitos, a interface apresenta uma mensagem de erro; após autenticação válida, a página passa a exibir o usuário conectado e seu perfil.

### Criar conta

A criação de conta é feita com um **código de convite**, nome de usuário, senha e confirmação da senha. A interface valida o preenchimento, impede o uso do nome reservado `admin`, exige uma senha com pelo menos seis caracteres e verifica se as senhas coincidem. O convite precisa ser válido para concluir o cadastro.

Após o login, a página exibe o nome e o perfil da conta, além da opção **Sair / Logout**.

## 2. Painel de Controle – Bancadas

Esta página organiza as bancadas por controlador e concentra os fluxos de cadastro e acompanhamento do cultivo.

### Bancadas cadastradas

- As bancadas são agrupadas pelo controlador ao qual estão associadas.
- A interface mostra a ocupação de cada controlador, com capacidade de até duas bancadas por controlador.
- Bancadas que não estejam vinculadas a um controlador aparecem em uma seção separada de aviso.
- Cada bancada pode ser expandida para consultar seus filetes e respectivas culturas, datas de plantio e previsões de colheita.
- Em uma bancada ainda em andamento, é possível adicionar um novo filete informando cultura e data de plantio.
- Um filete pode ser marcado como colhido. Quando todos os filetes cadastrados estão marcados como colhidos, a interface atualiza o estado da bancada para concluído.

### Cadastrar nova bancada

Na aba **Nova Bancada**, o formulário solicita:

1. Nome identificador da bancada.
2. Controlador disponível.
3. Cultura do primeiro filete.
4. Data de plantio do primeiro filete.

O cadastro exige um nome válido, uma cultura selecionada e uma data de plantio. Também é necessário que exista um controlador com vaga disponível. Ao salvar, a aplicação cria a bancada, associa o controlador e registra o primeiro filete.

Depois do cadastro, a interface tenta enviar os parâmetros da cultura ao Arduino associado e acompanha a resposta. Quando recebe confirmação, informa que os parâmetros foram enviados e confirmados; em caso de falha ou ausência de resposta dentro do período de espera, apresenta uma mensagem correspondente. A confirmação de recebimento não comprova, por si só, a eficácia agronômica da configuração nem o funcionamento físico de cada atuador.

## 3. Visão Geral

A Visão Geral foi concebida para uma consulta rápida do estado das bancadas sem precisar abrir cada série histórica.

- **Status das Bancadas:** apresenta o estado operacional mais recente disponível e o horário do último processamento registrado.
- **Indicadores por Bancada:** mostra valores recentes de pH, EC, temperatura da água, temperatura ambiente, umidade, luminosidade e estado do nível do tanque, conforme os dados disponíveis.
- **Alertas Ativos:** lista mensagens que exigem atenção. Quando não há alertas ativos registrados, a interface informa isso ao usuário.

Se ainda não houver bancadas cadastradas, ou se a conta não tiver acesso a uma bancada, a página mostra uma orientação em vez dos indicadores. Valores ausentes são apresentados como **Sem dados** quando não há uma leitura utilizável.

## 4. Monitoramento Detalhado

Esta página permite escolher uma bancada e examinar os dados e análises com mais contexto.

### Estado operacional

Quando existe um resultado processado, a interface apresenta o status consolidado, uma explicação do motivo, o período analisado, a quantidade de amostras consideradas e o horário do cálculo. O status consolidado atual é baseado em pH e condutividade elétrica (EC); as demais variáveis monitoradas não são automaticamente incorporadas a essa classificação.

### Gráficos e condições ambientais

A página oferece opções de visualização das séries de sensores e apresenta informações relacionadas ao ambiente e ao reservatório, incluindo temperatura ambiente, temperatura da água, umidade e estado da boia de nível. A disponibilidade dos gráficos depende da existência de leituras válidas.

### Anomalias

A seção de detecção de anomalias mostra desvios identificados nas leituras recentes, com informações como variável, desvio percentual e mensagem de diagnóstico. Se não houver amostras suficientes, a interface informa que ainda não é possível executar a análise; se nenhuma anomalia relevante for identificada, isso também é informado.

### Tendências operacionais

A seção de tendências resume o comportamento recente das variáveis, incluindo o estado da tendência, um indicador numérico e uma tabela com médias anteriores e recentes e variação percentual, quando esses dados estiverem disponíveis.

Uma tendência de subida ou descida descreve a variação observada e não significa necessariamente melhora ou piora para a cultura.

### Leituras recebidas

A área expansível **Ver leituras recebidas dos sensores** permite consultar os registros brutos disponíveis para a bancada selecionada. Ela é útil para verificar quais valores chegaram antes de interpretar os indicadores calculados.

## 5. Central de Ajuda — FAQ

A Central de Ajuda reúne explicações em quatro grupos:

- **Primeiros passos:** apresentação do sistema, escopo atual e cadastro de bancada/filete.
- **Sensores e dados:** variáveis recebidas, frequência de transmissão, armazenamento local e possíveis motivos para ausência de dados.
- **Indicadores e alertas:** status operacional, anomalias, tendências e interpretação dos alertas.
- **Automação e acesso:** atuação do Arduino, comunicação, perfis de acesso e simulador.

A FAQ deve ser consultada para entender os indicadores, mas a documentação técnica continua sendo a referência para detalhes de implementação e configuração.

## 6. Simulador de Leituras

O simulador é uma ferramenta de desenvolvimento, não uma fonte de telemetria real. No snapshot atual, o acesso é restrito ao ambiente de desenvolvimento e a contas com perfil de administrador.

A pessoa pode escolher uma bancada específica ou todas as bancadas cadastradas, definir a quantidade de leituras e o intervalo entre elas e optar por incluir valores fora do padrão. Durante a execução, a página mostra indicadores de pH, EC e temperatura da água, um gráfico de pH/EC, mensagens de andamento e uma barra de progresso. A execução também pode ser cancelada.

**Limitação importante:** na implementação analisada, a chamada que gravaria as leituras simuladas no banco está comentada. Portanto, o simulador serve para demonstrar a geração e a apresentação de valores fictícios na própria página; não se deve presumir que esses valores sejam persistidos ou que testem a comunicação física e os atuadores.

## 7. Controle de Acesso

Esta página é destinada ao gerenciamento de usuários por contas autorizadas.

### Usuários cadastrados

A aba de listagem apresenta totais de usuários por perfil e uma tabela com nome de usuário, e-mail e perfil. É possível filtrar pelo nome/e-mail e restringir a listagem a todos os perfis, administradores ou visualizadores.

### Novo convite

A aba de convite solicita o e-mail da pessoa e o perfil que será atribuído à conta. Ao enviar, a aplicação tenta gerar o convite e encaminhá-lo por e-mail; mensagens na interface indicam sucesso ou falha. O envio depende das configurações de e-mail do ambiente.

### Perfis apresentados pela interface

- **Administrador (`admin`):** pode executar tarefas administrativas, como gerenciar bancadas e convites, e acessar o simulador quando o ambiente também permite.
- **Visualizador (`viewer`):** perfil voltado à consulta das telas de acompanhamento, gráficos e alertas, sem as ações administrativas.

O acesso efetivo é controlado pelas regras de autorização implementadas na aplicação.

## Como interpretar mensagens e ausência de dados

- **Sem dados:** pode significar que ainda não chegaram leituras para a bancada ou que não há amostras suficientes para uma análise específica; isoladamente, não confirma uma falha de hardware.
- **Atenção / Crítico:** são classificações operacionais que devem ser interpretadas junto aos valores e aos limites da cultura configurada.
- **Sem anomalias:** significa que a rotina não encontrou anomalias relevantes na janela analisada; não é uma garantia de que todo o sistema esteja livre de problemas.
- **Confirmação de parâmetros pelo Arduino:** indica que a mensagem foi reconhecida pelo firmware, não que a correção tenha produzido o resultado agronômico esperado.
- **Dados simulados:** não representam medições reais e não devem ser usados como evidência de desempenho do cultivo.

## Organização dos arquivos da interface

A implementação visual fica principalmente em `app/`:

```text
app/
├── pages/       # Páginas acessadas pela navegação do Streamlit
├── components/  # Blocos reutilizáveis para painéis, indicadores e gráficos
└── assets/      # Imagens e outros recursos visuais
```

Os arquivos em `app/pages/` montam as páginas e recebem as interações do usuário. Os componentes em `app/components/` concentram partes reutilizáveis da apresentação, como os painéis de monitoramento e a renderização de filetes. O acesso a dados, a autenticação e as rotinas de análise são fornecidos pelos módulos do pacote `src/hydrotwin/`; seus detalhes estão descritos em [Organização do código e regras de negócio](software.md).

## Escopo e limites da interface

A interface apresenta dados recebidos e indicadores calculados pelo sistema. Ela não substitui a conferência física do cultivo, a calibração dos sensores nem a avaliação agronômica. O status consolidado atual utiliza pH e EC; anomalias e tendências são análises complementares independentes. A interface também não deve ser descrita como um modelo de simulação física de gêmeo digital ou como um sistema de previsão baseado em inteligência artificial.
