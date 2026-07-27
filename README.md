Aqui vai config básicas

e em breve um readme de verdade explicando o projeto

venv

.vscode

.git

requirements.txt

pyproject.toml

main

service

como instalar o projeto:

pip install -e .

como salvar dependencias:

pip freeze > requirements.txt

como instalar dependencias 

pip install -r requirements.txt


como criar env:

python -m venv venv

como ativar env:

.\venv\Scripts\activate

como rodar streamlit:

streamlit run main.py

---

hydrotwin.service

[Unit]
Description=Servico do Projeto de Automação Hidroponico
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/meu_projeto

# Aponta direto para o executável do Python DENTRO do venv

ExecStart=/home/pi/meu_projeto/.venv/bin/python main.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target

# Ajustar conforme necessário quando estiver no rasphydrotwin.service
