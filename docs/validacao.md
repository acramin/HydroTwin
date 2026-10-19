# Validação, testes e limitações

## Como interpretar esta página

A documentação combina inspeção estática do software e do firmware fornecido com informações de teste relatadas pela equipe. A comunicação serial bidirecional, a leitura dos sensores e o acionamento dos atuadores foram informados como funcionais no protótipo. Esses itens são registrados como validados conforme relato da equipe; os testes não foram repetidos durante esta revisão documental. Isso não comprova, por si só, ensaios exaustivos de robustez ou eficácia agronômica.

## Matriz de validação recomendada

| ID | Teste | Evidência mínima | Estado |
|---|---|---|---|
| V01 | Instalação limpa | Comandos, versão do Python e logs | Pendente de execução nesta auditoria |
| V02 | Inicialização segura do banco | Esquema criado sem apagar dados existentes | Pendente |
| V03 | Login e perfis | Casos admin/viewer e ambiente | Pendente |
| V04 | Comunicação serial bidirecional com Arduino físico | Mensagens de telemetria, envio de parâmetros e confirmações | Validado conforme informado pela equipe |
| V05 | Recepção por TCP com simulador | Cliente, mensagens e persistência | Pendente |
| V06 | Mensagem inválida | Log e ausência de registro incorreto | Pendente |
| V07 | Processamento de pH e EC | Entradas conhecidas e status esperado | Pendente |
| V08 | Anomalias | Pelo menos 30 valores e cálculo conferido | Pendente |
| V09 | Tendências | Pelo menos 60 valores e médias conferidas | Pendente |
| V10 | Envio de parâmetros e confirmação do firmware | Mensagem `PARAMS`, resposta `PARAMS_OK`/`PARAMS_ERROR` e timeout | Comunicação funcional conforme informado; cenários de falha pendentes |
| V11 | Perda e retorno de comunicação | Estado exibido e recuperação após interrupção | Pendente |
| V12 | Serviço Raspberry Pi | Inicialização, reinício e persistência | Pendente |
| V13 | Ensaio hidropônico e avaliação agronômica | Protocolo, duração, dados e resultados comparativos | Requer documentação dos resultados experimentais |

## Limitações técnicas observadas no snapshot

1. **Intervalo de processamento:** o valor executável em `reader.py` é 30 segundos; o comentário diz que seria 3600 segundos no sistema real. A versão implantada deve ser decidida e documentada explicitamente.
2. **Timestamp:** a telemetria recebe timestamp do relógio do receptor, enquanto defaults SQLite usam horário atual menos três horas. Uniformizar a estratégia antes de análise temporal rigorosa.
3. **Score consolidado:** o status consolidado é baseado em pH e EC. Scores de anomalia e tendência são armazenados separadamente, mas não compõem o score consolidado atual.
4. **Porta serial fixa:** `/dev/ttyACM0` e 9600 baud estão definidos no código do gerenciador; a adaptação para outros dispositivos exige alteração de configuração/código.
5. **Inicialização do banco:** no modo `DEVELOPMENT`, `init_db` apaga tabelas antes de recriá-las. Esse comportamento é perigoso para dados que se deseja preservar.
6. **Scripts de serviço:** os exemplos existentes apontam para `app.py` e caminhos genéricos; o ponto de entrada atual é `main.py`. Os exemplos precisam ser atualizados antes da implantação.
7. **Dependências:** `requirements.txt` está codificado em UTF-16 e inclui uma referência editável ao repositório; o arquivo deve ser normalizado e o fluxo de instalação padronizado.
8. **Testes automatizados:** o ZIP analisado não contém uma pasta de testes Python convencional. `pytest` aparece como dependência opcional, mas não se deve afirmar que existe uma suíte de testes passando sem adicioná-la e executá-la.
9. **Integridade referencial SQLite:** a conexão central não ativa `PRAGMA foreign_keys=ON` para cada conexão. Verificar e corrigir isso se as chaves estrangeiras forem requisito de integridade.
10. **Controle físico:** a equipe informa que sensores e atuadores foram ajustados e testados no protótipo. Para tornar a validação reproduzível, registrar versões de firmware/software, procedimento de calibração, condições de ensaio e evidências. A confirmação `PARAMS_OK` confirma o processamento da mensagem pelo firmware, não a eficácia agronômica da estratégia de dosagem.

## Evidências recomendadas para o TCC

- Versão do código (commit) e firmware testados;
- modelo dos sensores e método de calibração;
- amostras de mensagens de comunicação sem dados sensíveis;
- registros de banco que correspondam às mensagens recebidas;
- capturas de tela das páginas;
- logs de falhas e recuperação;
- duração do ensaio e número de amostras;
- tabelas/gráficos gerados a partir dos dados coletados;
- método de cálculo de cada métrica e limitações do experimento.

Não inserir valores hipotéticos como resultados experimentais. Se um teste ainda não ocorreu, identificá-lo como pendente.
