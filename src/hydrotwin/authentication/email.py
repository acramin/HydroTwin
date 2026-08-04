import smtplib
from email.message import EmailMessage
import os
from dotenv import load_dotenv

from hydrotwin.helpers.logger import logger
from hydrotwin.db.crud.usuario import code

load_dotenv(override=True)

def enviar_email_acesso(email):
    logger.debug("enviar_email_acesso()")

    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = os.getenv("SMTP_PORT")
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")
    smtp_to = email

    codigo_acesso = code
    link_acesso = "http://localhost:8501/"

    msg = EmailMessage()
    msg['Subject'] = '🚀 Bem-vindo à HydroTwin! Finalize seu pré-cadastro'
    msg['From'] = smtp_user
    msg['To'] = smtp_to

    # 1. Fallback em texto puro (para leitores que bloqueiam HTML)
    msg.set_content(f"""Olá!

Você foi pré-cadastrado na plataforma HydroTwin.

Para concluir seu cadastro, acesse: {link_acesso}
Seu código de acesso: {codigo_acesso}

Atenciosamente,
Equipe HydroTwin
""")

    # 2. Conteúdo em HTML estilizado (Inline CSS é essencial em e-mails)
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{
                font-family: 'Segoe UI', Arial, sans-serif;
                background-color: #f4f7f6;
                margin: 0;
                padding: 20px;
                color: #333333;
            }}
            .card {{
                max-width: 500px;
                background-color: #ffffff;
                margin: 0 auto;
                padding: 32px;
                border-radius: 10px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.08);
                border: 1px solid #e2e8f0;
            }}
            .header {{
                text-align: center;
                margin-bottom: 24px;
            }}
            .brand {{
                color: #0284c7;
                font-size: 26px;
                font-weight: bold;
                letter-spacing: -0.5px;
            }}
            .code-box {{
                background-color: #e0f2fe;
                border: 2px dashed #0284c7;
                color: #0369a1;
                font-size: 28px;
                font-weight: bold;
                letter-spacing: 4px;
                text-align: center;
                padding: 16px;
                border-radius: 8px;
                margin: 24px 0;
            }}
            .btn {{
                display: block;
                width: 220px;
                margin: 24px auto 0;
                padding: 12px 0;
                background-color: #0284c7;
                color: #ffffff !important;
                text-align: center;
                text-decoration: none;
                font-weight: 600;
                border-radius: 6px;
            }}
            .footer {{
                margin-top: 32px;
                padding-top: 16px;
                border-top: 1px solid #e2e8f0;
                font-size: 12px;
                color: #94a3b8;
                text-align: center;
            }}
        </style>
    </head>
    <body>
        <div class="card">
            <div class="header">
                <span class="brand">HydroTwin</span>
            </div>
            
            <h2 style="font-size: 20px; color: #1e293b; margin-top: 0;">Finalize seu cadastro 🎉</h2>
            
            <p style="line-height: 1.5; color: #475569;">
                Olá! Seu pré-cadastro foi realizado com sucesso pelo administrador.
            </p>
            <p style="line-height: 1.5; color: #475569;">
                Utilize o código de acesso abaixo para autenticar seu primeiro login na plataforma:
            </p>
            
            <div class="code-box">{codigo_acesso}</div>
            
            <a href="{link_acesso}" class="btn">Acessar Plataforma</a>
            
            <div class="footer">
                <p>Se você não esperava este e-mail, pode ignorá-lo com segurança.</p>
            </div>
        </div>
    </body>
    </html>
    """

    # Adiciona a versão HTML à mensagem
    msg.add_alternative(html_content, subtype='html')

    # Envio via SMTP + STARTTLS (porta 587)
    with smtplib.SMTP(smtp_host, int(smtp_port)) as smtp:
        smtp.starttls()
        smtp.login(smtp_user, smtp_pass)
        smtp.send_message(msg)