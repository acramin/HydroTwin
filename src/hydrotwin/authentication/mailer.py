import json
import os

from dotenv import load_dotenv
import requests

from hydrotwin.helpers.logger import logger

load_dotenv(override=True)


def enviar_email_acesso(email: str, codigo_acesso: str):
    """
    Envia um e-mail de convite contendo o código de primeiro acesso para o usuário.
    
    :param email: Endereço de e-mail do destinatário.
    :param codigo_acesso: Código de convite gerado para a liberação do cadastro.
    """
    logger.debug("enviar_email_acesso via Google Webhook Protegido")

    webhook_url = os.getenv("WEBHOOK_EMAIL_URL")
    webhook_token = os.getenv("WEBHOOK_SECRET_TOKEN")
    
    link_acesso = "http://localhost:8501/"  # Link local para desenvolvimento (alterar em produção)

    html_content = f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="utf-8"></head>
        <body style="font-family: Arial, sans-serif; background-color: #f4f7f6; padding: 20px;">
            <div style="max-width: 500px; background: #ffffff; padding: 30px; border-radius: 10px; margin: 0 auto; border: 1px solid #e2e8f0;">
                <h2 style="color: #0284c7;">HydroTwin &#x1F389;</h2>
                <p>Olá!</p>
                <p>Você recebeu um convite do administrador para acessar a plataforma <strong>HydroTwin</strong>.</p>
                <p>Utilize o código de acesso abaixo para realizar seu primeiro acesso:</p>
                <div style="background-color: #e0f2fe; border: 2px dashed #0284c7; color: #0369a1; font-size: 28px; font-weight: bold; letter-spacing: 4px; text-align: center; padding: 16px; border-radius: 8px; margin: 24px 0;">
                    {codigo_acesso}
                </div>
                <br>
                <a href="{link_acesso}" style="display: block; width: 220px; margin: 0 auto; background: #0284c7; color: white; text-align: center; padding: 12px 0; text-decoration: none; border-radius: 6px; font-weight: 600;">Acessar Plataforma</a>
                <p>Atenção: seu convite expira em 24 horas!</p>
            </div>
        </body>
        </html>
    """

    payload = {
        "token": webhook_token,
        "to": email,
        "subject": ">>> Convite de Acesso - HydroTwin <<<",
        "html": html_content,
    }

    json_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    headers = {"Content-Type": "application/json; charset=utf-8"}

    try:
        response = requests.post(
            webhook_url, data=json_bytes, headers=headers, timeout=15
        )

        # Log de validação
        if response.status_code == 200 and "sucesso" in response.text.lower():
            logger.info(f"E-mail de convite enviado com sucesso para {email}")
        else:
            logger.error(
                f"Erro de autenticação/envio no Webhook: {response.text}"
            )
            response.raise_for_status()

    except Exception as e:
        logger.error(f"Falha na requisição de e-mail para {email}: {e}")
        raise