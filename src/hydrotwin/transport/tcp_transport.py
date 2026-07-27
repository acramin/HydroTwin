import socket
import threading
from .base import Transporte
from hydrotwin.helpers.logger import logger


class TCPServerTransport(Transporte):

    def __init__(self, host="0.0.0.0", port=5000):
        self.host = host
        self.port = port
        self.servidor = None
        self.conn = None
        self.buffer = ""

        self._write_lock = threading.Lock()
        self._read_lock = threading.Lock()

    def conectar(self):
        try:
            # Cria e configura o socket do servidor
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # Permite reutilizar a porta imediatamente após fechar
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((self.host, self.port))
            s.listen(1)
            self.servidor = s
            logger.info(f"TCP Server ouvindo em {self.host}:{self.port}")

            # Bloqueia fora do Lock principal aguardando cliente
            conn, addr = self.servidor.accept()
            conn.settimeout(0.5)

            with self._read_lock, self._write_lock:
                self.conn = conn
                self.buffer = ""

            logger.info(f"Cliente conectado: {addr}")

        except Exception as e:
            self.fechar()
            raise ConnectionError(f"Falha na conexão do Servidor TCP: {e}")

    def enviar(self, mensagem: str):
        if not self.conn:
            raise RuntimeError("Nenhum cliente conectado")

        if not mensagem.endswith("\n"):
            mensagem += "\n"

        with self._write_lock:
            self.conn.sendall(mensagem.encode("utf-8"))

    def receber(self) -> str | None:
        if not self.conn:
            raise RuntimeError("Nenhum cliente conectado")

        with self._read_lock:
            # Retorna direto se já houver uma linha completa no buffer
            if "\n" in self.buffer:
                linha, self.buffer = self.buffer.split("\n", 1)
                return linha

            try:
                dados = self.conn.recv(1024)

                # Se dados vier vazio, a conexão foi encerrada pela outra ponta
                if not dados:
                    logger.warning("Conexão encerrada pelo cliente")
                    return None

                self.buffer += dados.decode("utf-8", errors="replace")

            except socket.timeout:
                return None  # Timeout normal para evitar travamento de thread

            if "\n" in self.buffer:
                linha, self.buffer = self.buffer.split("\n", 1)
                return linha

            return None

    def fechar(self):
        with self._write_lock, self._read_lock:
            if self.conn:
                try:
                    self.conn.shutdown(socket.SHUT_RDWR)
                except Exception:
                    pass
                self.conn.close()
                self.conn = None

            if self.servidor:
                self.servidor.close()
                self.servidor = None


class TCPClientTransport(Transporte):

    def __init__(self, host="127.0.0.1", port=5000):
        self.host = host
        self.port = port
        self.socket = None
        self.buffer = ""

        self._write_lock = threading.Lock()
        self._read_lock = threading.Lock()

    def conectar(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(3.0)  # Timeout para tentar conectar
            s.connect((self.host, self.port))
            s.settimeout(0.5)  # Timeout para leituras subsequentes

            with self._read_lock, self._write_lock:
                self.socket = s
                self.buffer = ""

            logger.info(f"Conectado ao servidor TCP em {self.host}:{self.port}")

        except Exception as e:
            self.fechar()
            raise ConnectionError(f"Falha ao conectar cliente TCP: {e}")

    def enviar(self, mensagem: str):
        if not self.socket:
            raise RuntimeError("Cliente TCP desconectado")

        if not mensagem.endswith("\n"):
            mensagem += "\n"

        with self._write_lock:
            self.socket.sendall(mensagem.encode("utf-8"))

    def receber(self) -> str | None:
        if not self.socket:
            raise RuntimeError("Cliente TCP desconectado")

        with self._read_lock:
            if "\n" in self.buffer:
                linha, self.buffer = self.buffer.split("\n", 1)
                return linha

            try:
                dados = self.socket.recv(1024)

                if not dados:
                    logger.warning("Conexão encerrada pelo servidor")
                    return None

                self.buffer += dados.decode("utf-8", errors="replace")

            except socket.timeout:
                return None

            if "\n" in self.buffer:
                linha, self.buffer = self.buffer.split("\n", 1)
                return linha

            return None

    def fechar(self):
        with self._write_lock, self._read_lock:
            if self.socket:
                try:
                    self.socket.shutdown(socket.SHUT_RDWR)
                except Exception:
                    pass
                self.socket.close()
                self.socket = None