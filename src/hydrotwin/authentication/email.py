import smtplib
from email.message import EmailMessage
import os
from dotenv import load_dotenv

from hydrotwin.helpers.logger import logger
from hydrotwin.db.crud.usuario import code

# Carrega as variáveis do arquivo .env da raiz
load_dotenv(override=True)

def enviar_email_acesso(email):
    logger.debug("enviar_email_acesso()")

    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = os.getenv("SMTP_PORT")
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")
    smtp_to = email

    msg = EmailMessage()
    msg['Subject'] = 'Finalize seu pré-cadastro na HydroTwin!'
    msg['From'] = smtp_user
    msg['To'] = smtp_to
    msg.set_content(f"""Olá! Por favor, finalize seu pré-cadastro na HydroTwin clicando no link abaixo:
                    \n\nhttp://localhost:8501/ 
                    \n\nInsira o código de acesso fornecido para completar o cadastro.
                    \n\nCódigo de Acesso: {code}
                    \n\nObrigado!""")

    # Envio via SMTP + STARTTLS (para porta 587)
    with smtplib.SMTP(smtp_host, int(smtp_port)) as smtp:
        smtp.starttls()  # Ativa a criptografia TLS
        smtp.login(smtp_user, smtp_pass)
        smtp.send_message(msg)
    
