from abc import ABC, abstractmethod

class Transporte(ABC):

    @abstractmethod
    def conectar(self):
        pass

    @abstractmethod
    def enviar(self, mensagem: str):
        pass

    @abstractmethod
    def receber(self) -> str:
        pass

    @abstractmethod
    def fechar(self):
        pass