# Contexto acadêmico e escopo

## Contexto e motivação

O HydroTwin integra um projeto de Trabalho de Conclusão de Curso voltado ao monitoramento e à supervisão de um sistema de cultivo hidropônico pela técnica NFT (*Nutrient Film Technique*). Nesse método, a solução nutritiva circula pelos canais de cultivo e retorna ao reservatório, permitindo sua reutilização.

O projeto parte da necessidade de acompanhar as condições físico-químicas e ambientais do cultivo de maneira estruturada, reduzindo a dependência de verificações exclusivamente manuais e facilitando a identificação de condições que demandem atenção. A proposta combina instrumentação eletrônica, processamento local de dados e uma interface de supervisão.

## Objetivo do software

O software HydroTwin tem como objetivo receber e persistir as leituras provenientes do sistema embarcado, processar os dados para identificar condições operacionais, anomalias e tendências e disponibilizar essas informações em uma interface de monitoramento.

A aplicação também contempla o gerenciamento das bancadas e culturas e o envio de parâmetros de cultivo ao controlador. O firmware C++ executado no Arduino Mega realiza a aquisição local e executa rotinas de controle de iluminação e dosagem nutricional. Conforme informado pela equipe, os sensores estão ajustados, as leituras são captadas corretamente, os atuadores operam como esperado e a comunicação serial bidirecional foi validada no protótipo.

## Escopo e limites

O HydroTwin deve ser entendido de acordo com o estágio real de implementação. A presença de rotinas analíticas, de comunicação e de configuração não constitui, isoladamente, evidência de que todos os mecanismos de automação foram validados experimentalmente.

A documentação distingue as funcionalidades implementadas, as integrações físicas confirmadas pela equipe e os testes de robustez ou avaliação experimental que ainda precisam de evidências específicas.

## Escopo funcional observado no código

- Cadastro de bancadas e filetes de cultivo.
- Associação de filetes a culturas e datas de plantio.
- Armazenamento de leituras brutas por bancada.
- Agregação estatística em janelas de processamento.
- Avaliação operacional com base em pH e EC.
- Cálculo de anomalias e tendências em séries históricas.
- Registro de alertas operacionais.
- Interface de monitoramento e gestão.
- Autenticação por usuário, convites e perfis.
- Envio de parâmetros de cultura ao microcontrolador.
- Simulação de telemetria para apoiar o desenvolvimento.

## Limites do escopo

O sistema não deve ser apresentado como um gêmeo digital completo, modelo preditivo ou sistema de controle agronômico validado sem evidências adicionais. No código atual, o status consolidado gravado em `sensor_proc` deriva da avaliação operacional de pH e EC; os resultados de anomalias e tendências são armazenados em campos próprios e não compõem esse score consolidado.

O software também não substitui a calibração dos sensores, a validação da segurança elétrica/hidráulica ou a avaliação agronômica. A existência de rotinas embarcadas e os testes funcionais relatados não substituem a apresentação dos procedimentos e resultados experimentais, nem demonstram por si só a eficácia agronômica de cada estratégia.

## Relação entre artigo e documentação técnica

O artigo acadêmico deve explicar o problema, a fundamentação, a metodologia, a montagem física e os resultados experimentais. A documentação do repositório explica a implementação e os passos necessários para reproduzir a instalação.

Antes da entrega final, alinhar entre artigo, firmware e software:
- sensores e modelos realmente utilizados;
- variáveis efetivamente transmitidas e armazenadas;
- periodicidade de aquisição e processamento;
- regras de classificação e limites de cultura;
- atuação física realizada pelo firmware;
- condições, duração e resultados dos testes.

## Divisão de responsabilidades

As responsabilidades principais foram distribuídas entre os integrantes, com colaboração conjunta na montagem e integração do protótipo:

- **Amanda — Software e computação:** autoria e desenvolvimento do software de supervisão HydroTwin, incluindo a aplicação Python/Streamlit, persistência em SQLite, processamento das leituras, interface e integração computacional.
- **Murilo — Hidráulica e instrumentação:** desenvolvimento da estrutura hidráulica e contribuição para a instrumentação relacionada ao sistema físico.
- **Matheus — Agronomia:** responsabilidade pela parte agronômica, incluindo aspectos das culturas e do cultivo hidropônico; também colaborou com atividades de montagem e integração não relacionadas diretamente ao desenvolvimento do software.
- **Enzo — Eletrônica:** desenvolvimento e integração dos componentes eletrônicos do protótipo.

O **firmware do Arduino** foi desenvolvido colaborativamente pela equipe ao longo do projeto e posteriormente refatorado com auxílio de ferramentas de inteligência artificial. A autoria do software de supervisão é distinta da autoria colaborativa do firmware. O artigo acadêmico é de autoria do grupo. Esta documentação técnica foi preparada por Amanda com auxílio de uma ferramenta de IA, cabendo à equipe revisar e validar seu conteúdo antes da publicação.

## Ambiente de execução e monitoramento remoto

O protótipo foi concebido para executar localmente, utilizando o Raspberry Pi 4 como unidade de processamento, o SQLite para persistência dos dados e o Streamlit para a interface de monitoramento.

Durante a experimentação, foi utilizado o ngrok para permitir o acesso remoto à interface, facilitando o acompanhamento das condições das bancadas sem a necessidade de acesso físico ao equipamento ou de conexão do dispositivo de monitoramento à mesma rede local.

Essa configuração não modifica a arquitetura de aquisição e processamento dos dados. O ngrok é empregado como recurso complementar de acesso remoto e pode ser substituído por outra solução de conectividade ou dispensado em instalações que utilizem somente o acesso local.
