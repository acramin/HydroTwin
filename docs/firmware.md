# Firmware do Arduino

## Responsabilidades

O firmware fornecido foi escrito em C++ para Arduino Mega 2560. Ele executa a leitura local dos sensores, envia telemetria ao Raspberry Pi, recebe parâmetros de cultura e controla saídas ligadas à iluminação e à dosagem nutricional. A equipe relata que sensores, comunicação serial bidirecional e atuadores foram ajustados e testados no protótipo.

O firmware foi desenvolvido colaborativamente pela equipe e posteriormente refatorado com auxílio de ferramentas de inteligência artificial. A autoria individual do software de supervisão Python não deve ser confundida com o desenvolvimento colaborativo do firmware.

## Sensores e telemetria

O código define duas configurações de bancada, B1 e B2, e usa os seguintes tipos de entrada:

- sensor analógico de pH;
- sensor analógico de condutividade elétrica (EC);
- LDR para estimativa de luminosidade;
- DHT11 para temperatura e umidade do ar;
- DS18B20 para temperatura da água;
- boia digital para indicação do nível do reservatório.

As leituras são atualizadas a cada 2 segundos e enviadas ao Raspberry Pi a cada 10 segundos. A serial é inicializada a 9600 baud. O formato emitido para cada bancada é equivalente a:

```text
B1: ARDUINO_01,<ph>,<ec>,<temperatura_ar>,<umidade>,<temperatura_agua>,<luminosidade>,<boia>
B2: ARDUINO_01,<ph>,<ec>,<temperatura_ar>,<umidade>,<temperatura_agua>,<luminosidade>,<boia>
```

Os valores entre sinais de menor/maior são marcadores explicativos, não texto literal. O estado da boia é transmitido como valor digital `0` ou `1`. O firmware fornecido não implementa leitura nem transmissão de vazão/fluxo; não documentar essa variável como telemetria ativa sem alteração e validação do código.

## Recepção de parâmetros

O Arduino recebe linhas iniciadas por `PARAMS,` e reconhece os campos `bancada_id`, `cultura_id`, `ph_min`, `ph_max`, `ec_min`, `ec_max`, `dias_ciclo`, `tempo_luz`, `lux_min` e `lux_max`. Há uma divergência de contrato no snapshot Python: o backend envia `tempo_luz_acesa`, enquanto o firmware procura `tempo_luz`. Assim, esse campo não é interpretado pelo firmware sem alinhar os nomes. Os parâmetros são armazenados em um de dois slots de hardware, associados à bancada. O firmware responde com `PARAMS_OK,bancada_id=<id>` ou `PARAMS_ERROR,...`.

A confirmação indica que a mensagem passou pela lógica de cadastro do firmware. Ela não deve ser interpretada isoladamente como prova de que cada atuador executou uma ação específica.

## Rotinas de controle presentes no código

- **Iluminação dimerizável:** utiliza PWM; quando não há limite `lux_max` positivo, define PWM máximo; quando a luminosidade estimada alcança o dobro de `lux_max`, reduz o PWM para aproximadamente metade.
- **Iluminação temporizada:** usa um ciclo fixo de 16 horas ligado e 8 horas desligado, implementado por temporização baseada em `millis()`.
- **Dosagem nutricional:** compara a EC medida com `ec_min` e, se estiver abaixo do alvo, calcula um tempo de acionamento da bomba com base nas constantes definidas no firmware, limitado a no máximo 5 segundos por acionamento.

Embora os parâmetros de pH sejam recebidos e armazenados, o código fornecido não implementa correção automática de pH. Os campos `tempo_luz_acesa` e `lux_min` também são armazenados, mas não participam das decisões descritas nas rotinas atuais. Portanto, a documentação não deve afirmar que esses parâmetros são efetivamente aplicados pelo firmware até que o código seja alterado e testado.

## Depuração serial

A constante `DEBUG` está definida como `true` no arquivo fornecido e mensagens de depuração são escritas na mesma serial usada para a telemetria e os comandos. O parser Python reconhece linhas `DEBUG`, mas a operação deve ser verificada para garantir que mensagens de diagnóstico não sejam confundidas com dados de telemetria. Antes de publicar uma versão de produção, considerar uma configuração de compilação que permita desabilitar logs ou separar canais de depuração.

## Validação e manutenção

A equipe informa que a leitura dos sensores, a comunicação serial bidirecional e o acionamento dos atuadores foram testados e funcionam no protótipo. Esta documentação não reproduziu os testes físicos. Para uma trilha de auditoria, versionar o sketch final no repositório (por exemplo, em `firmware/`), identificar a versão testada e registrar os procedimentos de calibração, evidências de telemetria e testes de interrupção/recuperação.
