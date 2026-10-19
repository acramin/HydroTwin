# Instalação e execução

## Requisitos

- Git;
- Python 3.9 ou superior, conforme declarado em `pyproject.toml`;
- pip e suporte a ambientes virtuais;
- permissões de leitura/escrita para o banco e diretório de logs;
- Arduino e acesso à porta serial, quando for testar a comunicação física.

## Clonar o projeto

```bash
git clone https://github.com/acramin/HydroTwin.git
cd HydroTwin
```

## Criar o ambiente virtual

Linux / Raspberry Pi:
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

Windows PowerShell:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

## Instalar dependências

Método recomendado para desenvolvimento a partir do `pyproject.toml`:

```bash
python -m pip install -e .
```

Para ferramentas de desenvolvimento:
```bash
python -m pip install -e ".[dev]"
```

O `requirements.txt` incluído está codificado como UTF-16 e contém um conjunto extenso de versões fixadas, além de uma instalação editável referenciada ao repositório remoto. Recomenda-se migrar esse arquivo para UTF-8 e definir um único fluxo oficial de dependências antes de usá-lo como caminho de instalação principal.

## Configurar `.env`

Copie `.env.example` para `.env` e ajuste os valores. Não versione `.env`.

```dotenv
DEFAULT_ADMIN_USERNAME=admin_local
DEFAULT_ADMIN_PASSWORD=troque_por_uma_senha_forte
SESSION_USER_KEY=chave_aleatoria_de_sessao
ENV_MODE=DEVELOPMENT
DB_NAME=hydroponic_test.db
TRANSPORT_MODE=tcp
```

O exemplo acima é apenas ilustrativo. No código:
- `ENV_MODE` aceita `DEVELOPMENT` ou `PRODUCTION`;
- `TRANSPORT_MODE` aceita `tcp` ou `serial`;
- sem `DB_NAME`, o nome padrão é `hydroponic_test.db` em desenvolvimento e `hydroponic.db` em produção;
- o caminho do banco é relativo ao diretório `src/hydrotwin/db/`, salvo se `DB_NAME` for um caminho absoluto;
- `SESSION_USER_KEY` define a chave usada em `st.session_state`;
- SMTP é opcional e usado para envio de logs críticos.

## Inicializar o banco de dados — atenção

O módulo de inicialização é executado por:

```bash
python -m hydrotwin.db.init_db
```

**Não execute esse comando sem entender o modo configurado.** Em `DEVELOPMENT`, o script chama `drop_tables()` antes de criar novamente as tabelas, o que pode apagar os dados existentes. Em `PRODUCTION`, se o arquivo do banco já existir, o script sai sem reinicializá-lo; se não existir, cria o esquema, o administrador e as culturas iniciais.

Antes de publicar uma instrução de instalação para usuários finais, é recomendável separar a criação inicial segura do esquema da rotina de reset de desenvolvimento.

## Executar a aplicação

Com o ambiente virtual ativo, a partir da raiz do repositório:

```bash
streamlit run main.py
```

`main.py` é o ponto de entrada da aplicação no snapshot revisado. Os exemplos atuais de `script/start.sh.example` e `depoly/hydrotwin.service.example` ainda apontam para `app.py`/`start.sh` em caminhos que não correspondem necessariamente ao layout atual; revise-os antes de utilizá-los.

## Modo de comunicação

### Simulador TCP
Configure `TRANSPORT_MODE=tcp`. O backend escuta em `0.0.0.0:65432`, e um cliente compatível deve conectar e enviar linhas no protocolo documentado. Como o bind TCP aceita conexões em interfaces de rede, utilize firewall e restrinja o acesso se não for necessário expor a porta.

### Arduino serial
Configure `TRANSPORT_MODE=serial`. O código utiliza `/dev/ttyACM0` e 9600 baud. No Windows ou em outras distribuições, a porta precisa ser adaptada no código/configuração; não existe variável de ambiente de porta serial no snapshot atual.

## Configuração opcional de acesso remoto

O HydroTwin pode ser utilizado sem acesso externo, diretamente na máquina em que está instalado ou por dispositivos autorizados na rede local.

Para permitir o monitoramento fora dessa rede, pode-se configurar o ngrok para encaminhar o acesso externo ao serviço Streamlit em execução no Raspberry Pi 4.

Essa etapa é opcional e não altera o funcionamento da comunicação com o Arduino, do processamento das leituras ou do banco de dados SQLite. A disponibilidade do acesso remoto depende de o Streamlit e o túnel estarem ativos e corretamente configurados.

Consulte [a documentação de implantação no Raspberry Pi](raspberry-pi.md) para obter as orientações relativas ao ambiente de execução.

## Verificações iniciais

- A aplicação abre sem exceções.
- O banco está no caminho esperado e possui o esquema correto.
- As credenciais e o perfil de usuário funcionam.
- O status de comunicação corresponde à conexão real.
- A telemetria válida é persistida uma única vez.
- A interface apresenta unidades e horários coerentes.
- O modo de desenvolvimento não é utilizado com dados que precisam ser preservados.

## Diagnóstico

**Não há dados:** verifique o modo de transporte, o firmware, o formato da linha e os logs.

**Porta serial indisponível:** confira o nome do dispositivo, permissões e se outro processo está usando a porta.

**Banco não encontrado:** confira `DB_NAME` e lembre que o caminho padrão está sob `src/hydrotwin/db/`.

**Erro em dependências:** utilize um ambiente virtual limpo e escolha um único método de instalação.

**Login automático inesperado:** verifique `ENV_MODE` e as credenciais configuradas.
