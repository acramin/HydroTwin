# Protocolo de comunicação

## Transporte

O modo é escolhido por `TRANSPORT_MODE`:
- `serial`: `/dev/ttyACM0`, 9600 baud (valores fixos no manager);
- `tcp`: servidor TCP em `0.0.0.0:65432` no manager.

As mensagens são linhas de texto terminadas por `\n`. O firmware usa `Serial.begin(9600)` e a aplicação Python usa 9600 baud no modo serial. A comunicação serial bidirecional com o Arduino físico foi validada pela equipe. O leitor centraliza o consumo da conexão e distribui os tipos de mensagem às filas apropriadas.

## Telemetria

O parser espera a seguinte ordem de campos:

```text
B<id>: <device_id>,<ph>,<ec>,<temperatura_ambiente>,<umidade>,<temperatura_agua>,<luminosidade>,<nivel_tanque>
```

Exemplo ilustrativo:

```text
B1: ARDUINO_01,6.1,1.4,23.5,60.0,20.1,800.0,1
```

A linha de exemplo é ilustrativa, não uma medição real. No firmware fornecido, o prefixo é `B1: ARDUINO_01` ou `B2: ARDUINO_01`; o parser Python usa o texto anterior aos dois-pontos como identificador da bancada. O timestamp é gerado pelo receptor (`datetime.now().isoformat()`). O último campo representa o estado digital da boia, embora o parser o armazene como valor numérico. O firmware envia o estado como `0` ou `1`.

## Mensagens de confirmação

O parser reconhece:
```text
PARAMS_OK,bancada_id=<id>
PARAMS_ERROR,bancada_id=<id>,motivo=<texto>
```

As confirmações são colocadas em `fila_confirmacao`. O sender aguarda até 10 segundos por uma confirmação correspondente à bancada enviada e atualiza o status do envio.

## Envio de parâmetros

O formato criado por `formatar_mensagem_parametros` é:

```text
PARAMS,bancada_id=<id>,cultura_id=<id>,ph_min=<valor>,ph_max=<valor>,ec_min=<valor>,ec_max=<valor>,dias_ciclo=<dias>,tempo_luz_acesa=<valor>,lux_min=<valor>,lux_max=<valor>
```

Os valores são buscados da tabela `cultura`. **Há uma divergência a corrigir entre o backend e o firmware:** o backend envia `tempo_luz_acesa`, mas o firmware fornecido procura `tempo_luz`. Por isso, esse parâmetro não é interpretado pelo firmware na versão analisada. O firmware reconhece `bancada_id`, `cultura_id`, `ph_min`, `ph_max`, `ec_min`, `ec_max`, `dias_ciclo`, `tempo_luz`, `lux_min` e `lux_max`, e responde com `PARAMS_OK` ou `PARAMS_ERROR`. A confirmação indica que a mensagem passou pela lógica de cadastro do firmware; por si só, não comprova que um atuador específico foi acionado com sucesso.

## Outras mensagens

O leitor reconhece linhas começando com `INIT_NODE` como cadastro de controlador e linhas iniciadas por `DEBUG` ou `---` como mensagens de depuração. O formato exato de `INIT_NODE` deve ser mantido consistente com o firmware.

## Regras de robustez

- Uma mensagem por linha.
- O parser rejeita telemetria com campos faltantes ou valores não numéricos.
- Mensagens desconhecidas são ignoradas com log de aviso.
- Telemetria e confirmações são encaminhadas para filas separadas.
- Se a fila estiver cheia, o código registra um aviso.
- O worker de conexão tenta reconectar em intervalos de 2 segundos e encerra após 50 tentativas consecutivas sem sucesso.
- A confirmação de envio tem timeout de 10 segundos.

A equipe informa que o envio e o recebimento serial foram testados no Arduino físico. Ainda é recomendável manter evidências versionadas (commit do software, versão do firmware e logs) e executar testes específicos de mensagens inválidas, perda de conexão e recuperação após falhas.
