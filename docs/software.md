# Organização do software e regras de negócio

## Ponto de entrada

`main.py`:
1. importa os serviços públicos do pacote `hydrotwin`;
2. inicia `hydrotwin.communication.manager.main` em uma thread daemon, guardada por `st.cache_resource`;
3. abre uma conexão SQLite para consultar o status da comunicação;
4. chama `bootstrap_auth()`;
5. registra as páginas Streamlit e monta a navegação conforme o perfil;
6. mostra o usuário, o papel, o status e o horário da última leitura;
7. executa a página selecionada.

## Organização de diretórios

| Caminho | Responsabilidade |
|---|---|
| `app/pages/` | Páginas Streamlit |
| `app/components/` | Componentes de visualização reutilizáveis |
| `app/assets/` | Recursos visuais |
| `src/hydrotwin/authentication/` | Autenticação, e-mail e acesso a páginas |
| `src/hydrotwin/communication/` | Filas, parser, leitor, sender e gerenciador |
| `src/hydrotwin/db/` | Conexão e inicialização do SQLite |
| `src/hydrotwin/db/crud/` | Operações de persistência |
| `src/hydrotwin/helpers/` | Variáveis de ambiente, formatação e logs |
| `src/hydrotwin/processing/` | Estado operacional, anomalias e tendências |
| `src/hydrotwin/tools/` | Simulador de Arduino e gerador de telemetria |
| `src/hydrotwin/transport/` | Transportes serial e TCP |

## Páginas da interface

- **HydroTwin:** entrada, login e cadastro via convite, além de apresentação do projeto.
- **Painel de Controle — Bancadas:** gestão de bancadas, controladores e filetes.
- **Visão Geral:** status por bancada, indicadores e alertas ativos.
- **Monitoramento Detalhado:** séries recentes, estatísticas e análises.
- **FAQ:** explicações de uso e interpretação.
- **Simulador:** geração de telemetria de teste; liberado conforme perfil e ambiente.
- **Controle de Acesso:** gestão de usuários e convites, acessível ao administrador.

## Perfis e ambiente

Os papéis previstos são `admin` e `viewer`. O administrador recebe acesso à gestão, monitoramento e controle de acesso; o viewer recebe acesso à visão geral, monitoramento detalhado e FAQ. A página Simulador é limitada ao ambiente `DEVELOPMENT`.

O módulo de autenticação pode efetuar login automático como administrador no modo de desenvolvimento quando as credenciais configuradas são válidas. Para produção, definir credenciais seguras e revisar o comportamento de bootstrap.

## Modelo de dados SQLite

O esquema atual cria as seguintes tabelas:

| Tabela | Finalidade |
|---|---|
| `bancada` | Cadastro da bancada e flag de conclusão |
| `filete` | Cultura, datas de plantio/colheita e situação do filete |
| `cultura` | Faixas ideais de pH/EC, ciclo e parâmetros de iluminação |
| `sensor_raw` | Leituras brutas recebidas por bancada |
| `sensor_proc` | Estatísticas agregadas, scores e status analíticos |
| `alerta` | Alertas operacionais e data de resolução |
| `usuario` | Conta, hash de senha, e-mail e papel |
| `convite` | Código, papel, estado e validade do convite |
| `sessao_usuario` | Token e validade da sessão |
| `controlador` | Controladores e associação de até duas bancadas |

O esquema define índices para consulta temporal das leituras brutas e processadas, filetes por bancada e alertas por bancada/estado.

### Granularidade dos dados

As leituras são associadas à bancada, não a cada filete individual. Os filetes armazenam a cultura e o calendário de cultivo; a leitura dos sensores não é individualizada por filete.

## Processamento de leituras

### Estatísticas

A função `processar_sensor` consulta leituras recentes para uma bancada e calcula mínimo, máximo e média das métricas numéricas: pH, EC, temperatura ambiente, temperatura da água, luminosidade, nível do tanque e umidade. O resultado é persistido em `sensor_proc`, junto ao número de amostras e à janela informada.

### Estado operacional

O estado operacional usa pH e EC. Os limites ideais são obtidos da cultura associada ao filete mais recente; se não houver limites disponíveis, o módulo possui valores padrão. A faixa de atenção é construída expandindo a faixa ideal em 20% da amplitude.

Cada variável é classificada como:
- **Saudável:** dentro da faixa ideal;
- **Atenção:** fora da faixa ideal, mas dentro da faixa expandida;
- **Crítico:** fora das faixas anteriores.

O status geral é o pior status entre as métricas avaliadas. Se não houver valores válidos, o resultado é `Sem dados`.

### Anomalias

`detectar_anomalias` exige por padrão pelo menos 30 valores válidos por métrica. Compara o último valor com a média dos valores anteriores da janela:
- desvio até 10%: saudável e não listado como anomalia;
- acima de 10% até 20%: atenção;
- acima de 20%: crítico.

O cálculo é heurístico e não equivale a um diagnóstico agronômico.

### Tendências

`analisar_tendencias` exige por padrão 60 valores válidos. Compara a média das 30 amostras anteriores com a média das 30 mais recentes:
- variação absoluta abaixo de 5%: estável;
- variação de 5% até menos de 20%: subindo ou descendo;
- variação absoluta de 20% ou mais: mudança brusca.

Tendências classificadas como estáveis não são incluídas na lista de tendências retornada.

### Consolidação e alertas

O score/status consolidado salvo em `sensor_proc` atualmente deriva do estado operacional baseado em pH e EC, com motivo fixo descrevendo essa origem. Anomalias e tendências são armazenadas em campos separados e não alteram esse score consolidado no código atual.

Os alertas abertos são sincronizados a partir do estado operacional. A página de visão geral consulta alertas cujo `dth_resolvido` está nulo.

## Integração com o firmware

O software Python executado no Raspberry Pi e o firmware C++ executado no Arduino têm responsabilidades distintas. O firmware fornecido lê sensores aproximadamente a cada 2 segundos, envia uma linha de telemetria por bancada a cada 10 segundos e recebe mensagens `PARAMS` pela serial. O backend recebe as leituras, persiste os valores e executa as análises descritas acima.

No firmware fornecido, a telemetria contém pH, EC, temperatura do ar, umidade relativa, temperatura da água, luminosidade e estado da boia de nível. Não há leitura de fluxo no código analisado. Embora o protocolo aceite parâmetros de pH, o controle de dosagem mostrado no firmware usa `ec_min` como alvo; não há uma rotina de correção de pH nesse código. A rotina de iluminação usa `lux_max` e um ciclo fixo de 16 horas ligado/8 horas desligado; os campos `tempo_luz_acesa` e `lux_min` são recebidos e armazenados, mas não são usados nas decisões visíveis do firmware fornecido.

A equipe informa que os sensores e atuadores estão ajustados e que a comunicação serial bidirecional funciona no protótipo. A interpretação dos valores analógicos e a eficácia das regras de controle devem ser descritas no relatório experimental com os procedimentos de calibração e teste correspondentes. Consulte [Firmware do Arduino](firmware.md) para o detalhamento do comportamento embarcado.

## Intervalos e relógio

No snapshot revisado, `communication/reader.py` define:
- processamento periódico a cada **30 segundos**;
- timeout do monitor de comunicação de **1200 segundos (20 minutos)**.

O comentário no código indica que o intervalo de processamento seria aumentado para uma hora no sistema real, mas o valor executável atual é 30 segundos. A telemetria usa `datetime.now().isoformat()` no momento em que é recebida pelo Raspberry Pi. Os defaults SQLite usam `datetime('now', '-3 hours')`. Essa mistura de estratégias de timestamp deve ser revista para manter consistência.

## Logs

`helpers/logger.py` configura logs no terminal e em `logs/app.log`, com rotação diária e retenção de 30 arquivos. Em `PRODUCTION`, o terminal usa nível INFO; em outros modos, DEBUG. Se as variáveis SMTP necessárias estiverem preenchidas, eventos `CRITICAL` também podem ser enviados por e-mail.

Os caminhos de log são relativos ao diretório de trabalho do processo. A implantação por serviço deve definir `WorkingDirectory` explicitamente.
