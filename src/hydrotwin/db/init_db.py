import sys

from hydrotwin.helpers.env import is_production_mode, is_development_mode
from hydrotwin.helpers.logger import logger
from hydrotwin.db.conn import DB_PATH
from hydrotwin.db.crud.base import drop_tables, create_tables
from hydrotwin.db.crud.cultura import insert_culturas
from hydrotwin.db.crud.usuario import ensure_default_admin

if __name__ == "__main__":
    try:
        if is_production_mode() and DB_PATH.exists():
            logger.warning("Modo de produção detectado. O banco de dados não será reinicializado para evitar perda de dados.")
            sys.exit(0)

        elif is_development_mode() or (is_production_mode() and not DB_PATH.exists()):
            logger.info("Iniciando preparação do banco de dados...")
            drop_tables()
            logger.info("Tabelas deletadas (se existiam).")
            create_tables()
            logger.info("Banco criado com sucesso!")
            ensure_default_admin()
            logger.info("Usuário admin garantido!")
            insert_culturas()
            logger.info("Culturas inseridas com sucesso!")

    except Exception as e:
        logger.critical(f"Falha na inicialização do banco de dados: {e}", exc_info=True)
        sys.exit(1)