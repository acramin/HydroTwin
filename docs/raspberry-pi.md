# Implantação no Raspberry Pi

## Objetivo

Executar a interface e o backend do HydroTwin localmente no Raspberry Pi, com inicialização persistente por `systemd`. Os caminhos, usuário do serviço e dispositivo serial variam conforme a instalação.

## Preparação

1. Instale Git e uma versão compatível do Python.
2. Clone o repositório em um diretório persistente.
3. Crie `.venv` e instale as dependências.
4. Crie e revise o `.env`.
5. Confirme o caminho e as permissões do banco SQLite.
6. Teste a aplicação manualmente com `streamlit run main.py`.
7. Teste o Arduino e o transporte escolhido antes de habilitar o serviço.

## Porta serial

O manager utiliza `/dev/ttyACM0` a 9600 baud no modo serial. Confirme o dispositivo real no Raspberry Pi e adapte `src/hydrotwin/communication/manager.py` caso necessário. Garanta que o usuário do serviço tenha acesso à porta e que nenhum outro processo abra a mesma conexão.

## Script de inicialização

O arquivo atual `script/start.sh.example` é um modelo antigo: utiliza caminhos ilustrativos, procura `venv/` e executa `app.py`, enquanto o ponto de entrada atual é `main.py`. Não o use sem revisão.

Modelo sugerido para `script/start.sh` depois de ajustar o caminho do projeto:

```bash
#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="/CAMINHO/ABSOLUTO/HydroTwin"
cd "$PROJECT_DIR"

exec "$PROJECT_DIR/.venv/bin/streamlit" run "$PROJECT_DIR/main.py" \
  --server.headless true \
  --server.port 8501
```

O script não inicializa nem apaga o banco de dados. A preparação do banco deve ser uma etapa explícita e separada.

Dê permissão de execução:
```bash
chmod +x script/start.sh
```

## Serviço systemd

Modelo sugerido, adaptado ao caminho real:

```ini
[Unit]
Description=HydroTwin - supervisao hidropônica local
After=multi-user.target

[Service]
Type=simple
User=USUARIO_DO_SISTEMA
WorkingDirectory=/CAMINHO/ABSOLUTO/HydroTwin
EnvironmentFile=/CAMINHO/ABSOLUTO/HydroTwin/.env
Environment=PYTHONUNBUFFERED=1
ExecStart=/CAMINHO/ABSOLUTO/HydroTwin/script/start.sh
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Salve o arquivo como `/etc/systemd/system/hydrotwin.service`, revise usuário e caminhos e execute:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now hydrotwin.service
sudo systemctl status hydrotwin.service
journalctl -u hydrotwin.service -f
```

Para reiniciar:
```bash
sudo systemctl restart hydrotwin.service
```

## Disponibilização da interface por meio do ngrok

O HydroTwin pode ser executado localmente no Raspberry Pi 4, com acesso remoto opcional à interface Streamlit por meio do [ngrok](https://ngrok.com/). O ngrok cria um túnel entre um endereço externo e a porta local em que a aplicação está disponível.

Essa configuração é opcional: o acesso local ao HydroTwin não depende do ngrok.

### 1. Instalação e configuração

Instale o ngrok no ambiente responsável pelo túnel seguindo o procedimento oficial:

[Documentação oficial — disponibilizar serviços locais](https://dashboard.ngrok.com/get-started/share-localhost).

Após a instalação, configure o token de autenticação da sua própria conta:

```plaintext
ngrok config add-authtoken SEU_AUTHTOKEN

```

Não utilize o token de outra pessoa nem versione credenciais reais no repositório.

### 2. Arquivo de configuração

O projeto disponibiliza um exemplo de configuração em `ngrok.yml`. O arquivo define o endpoint, o endereço externo e o destino local das requisições.

Exemplo:

```plaintext
version: "3"

agent:
  authtoken: SEU_AUTHTOKEN

endpoints:
  - name: project_name
    url: https://your_domain.com
    upstream:
      url: http://localhost:8501

```

Os valores do exemplo devem ser adaptados ao ambiente utilizado:

- `authtoken`: token da conta ngrok, caso a autenticação seja configurada diretamente no arquivo.
- `name`: nome usado para identificar o endpoint na inicialização.
- `url`: endereço público configurado na conta ngrok, quando aplicável.
- `upstream.url`: endereço e porta em que a interface Streamlit está sendo executada.

No exemplo, a porta `8501` é a porta padrão do Streamlit. Se a aplicação utilizar outra porta, atualize o destino do túnel.

**Segurança:** se o arquivo contiver um token real, não o publique no Git. Prefira manter um arquivo de exemplo sem credenciais e configurar os dados privados separadamente.

### 3. Inicialização

Inicie o HydroTwin no Raspberry Pi utilizando o procedimento descrito na documentação de instalação. Confirme que o Streamlit está funcionando na porta configurada.

Em seguida, inicie o endpoint pelo terminal:

```plaintext
ngrok start project_name
```

O nome `project_name` deve corresponder ao campo `name` definido no arquivo de configuração. Se o arquivo estiver em um caminho não padrão, consulte a documentação do ngrok para informar explicitamente sua localização.

### 4. Verificação do acesso

Após iniciar o túnel:

1. Verifique se o ngrok informa que o endpoint está ativo.
2. Acesse o endereço externo configurado.
3. Confirme que a página de autenticação do HydroTwin é apresentada.
4. Entre com uma conta autorizada e verifique se as páginas correspondem às permissões desse usuário.

Se o acesso não funcionar, confira se o Streamlit está em execução, se a porta de destino está correta e se o endereço externo e o endpoint correspondem à configuração da sua conta.

### 5. Limitações e segurança

O ngrok fornece um caminho de acesso remoto à interface, mas não substitui a autenticação e a autorização implementadas pelo HydroTwin. Antes de disponibilizar o sistema externamente, verifique se essas proteções estão habilitadas e se as credenciais não estão expostas.

A indisponibilidade do túnel interrompe o acesso por esse endereço externo, mas não implica, por si só, a interrupção da aquisição e do processamento local dos dados.

O ngrok é uma alternativa de acesso remoto para experimentação e demonstração. Ele não é obrigatório para executar o sistema na rede local.

## Persistência e segurança

- Não use caminhos temporários para o banco.
- Restrinja permissões de `.env`.
- Faça backup antes de atualizar o código ou o banco.
- Não inicie `python -m hydrotwin.db.init_db` automaticamente em cada boot: no modo `DEVELOPMENT`, o script apaga e recria as tabelas.
- O Streamlit usa porta 8501 no exemplo. Mantenha o acesso local ou proteja a interface e a porta conforme a política de rede do ambiente.
- Verifique o reinício após queda de energia e a recuperação da comunicação serial.
- Os logs são relativos ao diretório de trabalho; `WorkingDirectory` deve apontar para a raiz do projeto.
- Não publique tokens do ngrok, credenciais de acesso ou arquivos de configuração que contenham segredos no repositório.

## Checklist

- [ ] Ambiente virtual e dependências instalados.
- [ ] `.env` preenchido e protegido.
- [ ] Banco persistente inicializado conscientemente.
- [ ] Porta serial verificada.
- [ ] Script usa `main.py` e `.venv`.
- [ ] Serviço executa com usuário sem privilégios desnecessários.
- [ ] Serviço inicia após reboot.
- [ ] Logs acessíveis pelo journal e arquivo.
- [ ] Comunicação validada com o Arduino físico.
- [ ] Backup e restauração testados.
