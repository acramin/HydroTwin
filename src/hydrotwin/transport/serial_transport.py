import serial
import time
import threading
from .base import Transporte
from hydrotwin.helpers.logger import logger

class SerialTransport(Transporte):

    def __init__(self, porta, baud_rate=9600):
        logger.debug("__init__(self, porta, baud_rate=9600)")
        self.porta = porta
        self.baud_rate = baud_rate
        self.serial = None
        
        # Locks separadas para evitar que a leitura bloqueie o envio
        self._write_lock = threading.Lock()
        self._read_lock = threading.Lock()

    def conectar(self):
        logger.debug("conectar(self)")
        try:
            # Inicializa a conexão
            s = serial.Serial(
                self.porta,
                self.baud_rate,
                timeout=0.5
            )
            
            # Aguarda a estabilização do dispositivo (ex: reset do Arduino)
            time.sleep(2)
            
            s.reset_input_buffer()
            self.serial = s
            logger.info(f"Serial conectada em {self.porta}")

        except serial.SerialException as e:
            self.serial = None
            raise ConnectionError(
                f"Falha ao conectar serial em {self.porta}: {e}"
            )

    def enviar(self, mensagem: str):
        logger.debug("enviar(self, mensagem: str)")
        if not self.serial or not self.serial.is_open:
            raise RuntimeError("Serial desconectada")

        if not mensagem.endswith("\n"):
            mensagem += "\n"

        with self._write_lock:
            self.serial.write(mensagem.encode("utf-8"))
            self.serial.flush()

    def receber(self) -> str | None:
        logger.debug("receber(self) -> str | None")
        if not self.serial or not self.serial.is_open:
            raise RuntimeError("Serial desconectada")

        with self._read_lock:
            dados = self.serial.readline()

        if not dados:
            return None

        # Substitui caracteres inválidos sem derrubar a mensagem inteira
        return dados.decode("utf-8", errors="replace").strip()

    def fechar(self):
        logger.debug("fechar(self)")
        # Garante a finalização de leituras e escritas antes de fechar
        with self._write_lock, self._read_lock:
            if self.serial and self.serial.is_open:
                self.serial.close()
            self.serial = None

    # Suporte ao Context Manager (opcional, mas recomendado)
    def __enter__(self):
        logger.debug("__enter__(self)")
        self.conectar()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        logger.debug("__exit__(self, exc_type, exc_val, exc_tb)")
        self.fechar()