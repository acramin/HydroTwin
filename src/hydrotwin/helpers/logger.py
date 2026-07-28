import logging
from logging.handlers import TimedRotatingFileHandler, SMTPHandler
import sys
import os
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env da raiz
load_dotenv(override=True)

import time
from logging import Filter

class DuplicateFilter(Filter):

    def __init__(self, interval_seconds=60):
        super().__init__()
        self.interval_seconds = interval_seconds
        self.last_logged = {}

    def filter(self, record):
        # Usa a mensagem como chave para identificar repetições
        msg = record.getMessage()
        now = time.time()

        if msg in self.last_logged:
            if now - self.last_logged[msg] < self.interval_seconds:
                return False  # Bloqueia o log (muito recente)

        self.last_logged[msg] = now
        return True  # Permite o log


import threading
import asyncio

def setup_global_exception_handlers():
    """
    Redireciona todas as exceções não tratadas do Python para o Logger.
    """

    # 1. Captura erros em código Síncrono e Thread Principal
    def handle_sys_exception(exc_type, exc_value, exc_traceback):
        # Permite que o Ctrl+C (KeyboardInterrupt) encerre o programa normalmente
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        logging.critical(
            "Exceção não tratada (Main Thread):", 
            exc_info=(exc_type, exc_value, exc_traceback)
        )

    sys.excepthook = handle_sys_exception


    # 2. Captura erros em Threads Secundárias (threading)
    def handle_thread_exception(args):
        if issubclass(args.exc_type, KeyboardInterrupt):
            return

        logging.critical(
            f"Exceção não tratada na Thread [{args.thread.name}]:", 
            exc_info=(args.exc_type, args.exc_value, args.exc_traceback)
        )

    threading.excepthook = handle_thread_exception


    # 3. Captura erros dentro do Event Loop do Asyncio
    def handle_async_exception(loop, context):
        exception = context.get("exception")
        message = context.get("message")
        
        # Trata ou silencia erros comuns de desconexão no Windows se desejar
        if isinstance(exception, ConnectionResetError):
            logging.warning(f"Conexão encerrada pelo host remoto no asyncio: {exception}")
            return

        logging.critical(
            f"Exceção não tratada no Asyncio: {message}", 
            exc_info=exception
        )

    # Aplica o handler do asyncio no loop atual
    try:
        loop = asyncio.get_running_loop()
        loop.set_exception_handler(handle_async_exception)
    except RuntimeError:
        # Se o loop ainda não estiver rodando, pode registrar quando iniciar o asyncio.run()
        pass

def setup_logger():
    # Cria o logger raiz do seu projeto
    logger = logging.getLogger("hydrotwin")
    logger.setLevel(logging.DEBUG)

    # Evita duplicar logs se a função for chamada mais de uma vez
    if logger.hasHandlers():
        return logger

    # Adiciona o filtro para evitar mensagens idênticas em menos de 60 segundos
    duplicate_filter = DuplicateFilter(interval_seconds=60) # pensar em um tempo bom para colocar aqui
    logger.addFilter(duplicate_filter)

    # Formato das mensagens
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # 1. TERMINAL (Mostra tudo: DEBUG para cima)
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.DEBUG)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    # 2. ARQUIVO DIÁRIO (Salva INFO para cima)
    # 'when="midnight"' rotaciona à meia-noite. 'interval=1' significa a cada 1 dia.
    # 'backupCount=30' guarda o histórico dos últimos 30 dias.
    file_handler = TimedRotatingFileHandler(
        'app.log',
        when='midnight',
        interval=1,
        backupCount=30,
        encoding='utf-8'
    )
    file_handler.suffix = "%Y-%m-%d"  # O arquivo antigo vira app.log.2026-07-25
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # 3. E-MAIL (Apenas para erros CRITICAL)
    # IMPORTANTE: Configure com os dados reais do seu servidor SMTP (Ex: Mailgun, SendGrid, Gmail)
    try:
        
        info = [os.getenv("SMTP_HOST"), 
                os.getenv("SMTP_PORT"),
                os.getenv("SMTP_USER"),
                os.getenv("SMTP_PASS"),
                os.getenv("SMTP_TO")]

        email_handler = SMTPHandler(
            mailhost=(info[0], info[1]),       # Servidor SMTP e Porta
            fromaddr=info[2],            # Remetente
            toaddrs=[info[4]],             # Destinatário(s)
            subject='[ALERTA CRÍTICO] Falha no Sistema',  # Assunto do e-mail
            credentials=(info[2], info[3]),   # Login e Senha
            secure=()                                     # Ativa TLS/SSL automático
        )
        email_handler.setLevel(logging.CRITICAL)          # SÓ envia e-mail se for CRITICAL
        email_handler.setFormatter(formatter)
        logger.addHandler(email_handler)
    except Exception as e:
        logger.warning(f"Não foi possível configurar o SMTPHandler: {e}")

    # ATIVA OS HOOKS GLOBAIS DE EXCEÇÃO
    setup_global_exception_handlers()

    return logger

# Inicializa o logger para que ele possa ser importado diretamente
try: 
    logger = setup_logger()
    logger.info("Logger iniciado com sucesso!")
except Exception as e:
    print("erro ou criar logger:", e)
