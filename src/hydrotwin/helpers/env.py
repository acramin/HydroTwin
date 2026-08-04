import os
from functools import lru_cache
from dotenv import load_dotenv
from hydrotwin.helpers.logger import logger

load_dotenv(override=True)

ENV_MODE_DEVELOPMENT = "DEVELOPMENT"
ENV_MODE_PRODUCTION = "PRODUCTION"
VALID_ENV_MODES = {ENV_MODE_DEVELOPMENT, ENV_MODE_PRODUCTION}
DEFAULT_ENV_MODE = ENV_MODE_DEVELOPMENT
DB_NAME_DEVELOPMENT = "hydroponic_test.db"
DB_NAME_PRODUCTION = "hydroponic.db"

@lru_cache(maxsize=1)
def get_env_mode():
    logger.debug("get_env_mode()")
    env_mode = (os.getenv("ENV_MODE") or DEFAULT_ENV_MODE).strip().upper()
    if env_mode not in VALID_ENV_MODES:
        logger.warning(f"ENV_MODE '{env_mode}' inválido. Usando valor padrão '{DEFAULT_ENV_MODE}'.")
        return DEFAULT_ENV_MODE
    logger.info(f"ENV_MODE definido como '{env_mode}'.")
    return env_mode

def is_development_mode():
    logger.debug("is_development_mode()")
    return get_env_mode() == ENV_MODE_DEVELOPMENT

def is_production_mode():
    logger.debug("is_production_mode()")
    return get_env_mode() == ENV_MODE_PRODUCTION

def get_db_name():
    logger.debug("get_db_name()")
    db_name = os.getenv("DB_NAME")
    if db_name:
        logger.info(f"DB_NAME definido como '{db_name}' via variável de ambiente.")
        return db_name
    if is_development_mode():
        logger.info(f"Modo de desenvolvimento detectado. Usando banco de dados '{DB_NAME_DEVELOPMENT}'.")
        return DB_NAME_DEVELOPMENT
    else:
        logger.info(f"Modo de produção detectado. Usando banco de dados '{DB_NAME_PRODUCTION}'.")
        return DB_NAME_PRODUCTION
    
def get_admin_credentials():
    logger.debug("get_admin_credentials()")
    return (
        os.getenv("DEFAULT_ADMIN_USERNAME"),
        os.getenv("DEFAULT_ADMIN_PASSWORD")
    )
    
def user_session_key():
    logger.debug("user_session_key()")
    return os.getenv("SESSION_USER_KEY")

def get_transport_mode():
    logger.debug("get_transport_mode()")
    transport_mode = (os.getenv("TRANSPORT_MODE") or "tcp").strip().lower()
    if transport_mode not in {"tcp", "serial"}:
        logger.warning(f"TRANSPORT_MODE '{transport_mode}' inválido. Usando 'tcp'.")
        return "tcp"
    logger.info(f"TRANSPORT_MODE definido como '{transport_mode}'.")
    return transport_mode