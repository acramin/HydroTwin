import sqlite3
from pathlib import Path
from hydrotwin.helpers.env import get_db_name

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / get_db_name()

def conectar_db():
    """
    Função centralizadora para abrir conexão com banco de dados
    """
    #print(DB_PATH)
    # Garante que a pasta 'dados/' exista
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    return sqlite3.connect(DB_PATH)