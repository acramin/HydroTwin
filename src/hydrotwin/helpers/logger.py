import asyncio
import logging
from logging import Filter
from logging.handlers import SMTPHandler, TimedRotatingFileHandler
import os
import sys
import threading
import time
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env da raiz
load_dotenv(override=True)

class DuplicateFilter(Filter):

    def __init__(self, interval_seconds=60):
        super().__init__()
        self.interval_seconds = interval_seconds
        self.last_logged = {}

    def filter(self, record):
        msg = record.getMessage()
        now = time.time()

        # Usamos o nome do arquivo, a linha e a mensagem como chave única
        key = (record.filename, record.lineno, msg)

        if key in self.last_logged:
            if now - self.last_logged[key] < self.interval_seconds:
                return False  # Bloqueia o log recente

        self.last_logged[key] = now
        return True  # Permite o log

def setup_global_exception_handlers():
    """Redireciona todas as exceções não tratadas do Python para o Logger."""

    # 1. Thread Principal (Síncrono)
    def handle_sys_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        logging.critical(
            "Exceção não tratada (Main Thread):",
            exc_info=(exc_type, exc_value, exc_traceback),
        )

    sys.excepthook = handle_sys_exception

    # 2. Threads Secundárias
    def handle_thread_exception(args):
        if issubclass(args.exc_type, KeyboardInterrupt):
            return

        logging.critical(
            f"Exceção não tratada na Thread [{args.thread.name}]:",
            exc_info=(args.exc_type, args.exc_value, args.exc_traceback),
        )

    threading.excepthook = handle_thread_exception

    # 3. Asyncio Event Loop
    def handle_async_exception(loop, context):
        exception = context.get("exception")
        message = context.get("message")

        if isinstance(exception, ConnectionResetError):
            logging.warning(
                f"Conexão encerrada pelo host remoto no asyncio: {exception}"
            )
            return

        logging.critical(
            f"Exceção não tratada no Asyncio: {message}", exc_info=exception
        )

    try:
        loop = asyncio.get_running_loop()
        loop.set_exception_handler(handle_async_exception)
    except RuntimeError:
        pass


def setup_logger():
    logger = logging.getLogger("hydrotwin")
    logger.setLevel(logging.DEBUG)

    if logger.hasHandlers():
        return logger

    # Filtro anti-duplicados
    duplicate_filter = DuplicateFilter(interval_seconds=60)
    logger.addFilter(duplicate_filter)

    # Novo formato: inclui [arquivo.py:linha] e a função (opcional)
    # Exemplo de saída: 2026-07-28 17:00:00,123 - hydrotwin - [services.py:42] - INFO - Mensagem aqui
    log_format = "%(asctime)s - %(name)s - [%(filename)s:%(lineno)d] - %(levelname)s - %(message)s"
    formatter = logging.Formatter(log_format)

    # 1. TERMINAL (Console)
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.DEBUG)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    # 2. ARQUIVO DIÁRIO
    file_handler = TimedRotatingFileHandler(
        "app.log",
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8",
    )
    file_handler.suffix = "%Y-%m-%d"
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # 3. E-MAIL (Alertas CRITICAL)
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = os.getenv("SMTP_PORT")
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")
    smtp_to = os.getenv("SMTP_TO")

    if all([smtp_host, smtp_port, smtp_user, smtp_pass, smtp_to]):
        try:
            email_handler = SMTPHandler(
                mailhost=(smtp_host, int(smtp_port)),
                fromaddr=smtp_user,
                toaddrs=[smtp_to],
                subject="[ALERTA CRÍTICO] Falha no Sistema",
                credentials=(smtp_user, smtp_pass),
                secure=(),
            )
            email_handler.setLevel(logging.CRITICAL)
            email_handler.setFormatter(formatter)
            logger.addHandler(email_handler)
        except Exception as e:
            logger.warning(f"Não foi possível configurar o SMTPHandler: {e}")
    else:
        logger.warning(
            "Variáveis de ambiente SMTP incompletas. Envio de e-mails desativado."
        )

    setup_global_exception_handlers()
    return logger


try:
    logger = setup_logger()
    logger.info("Logger iniciado com sucesso!")
except Exception as e:
    print("Erro ao criar logger:", e)