import streamlit as st

from hydrotwin.db.crud.usuario import autenticar_usuario, ensure_default_admin
from hydrotwin.helpers.env import is_development_mode, user_session_key, get_admin_credentials
from hydrotwin.helpers.logger import logger

SESSION_USER_KEY = user_session_key()

def bootstrap_auth():
    ensure_default_admin()
    logger.debug("bootstrap_auth()")

    if SESSION_USER_KEY not in st.session_state:
        st.session_state[SESSION_USER_KEY] = None
        logger.debug("SESSION_USER_KEY adicionada ao session_state.")
    
    # Em modo DEVELOPMENT, fazer login automático como admin se não houver usuário logado
    if is_development_mode() and st.session_state[SESSION_USER_KEY] is None:
        try:
            usuario = autenticar_usuario(
                *get_admin_credentials()
            )
            if usuario:
                st.session_state[SESSION_USER_KEY] = usuario
                logger.debug("Dev mode auto login!")
        except Exception:
            logger.debug("Sem auto login!")
            pass  # Se falhar, continua sem login automático


def get_current_user():
    bootstrap_auth()
    logger.debug("get_current_user()")
    return st.session_state.get(SESSION_USER_KEY)


def set_current_user(user):
    logger.debug("set_current_user()")
    st.session_state[SESSION_USER_KEY] = user


def logout_user():
    logger.debug("logout_user()")
    st.session_state[SESSION_USER_KEY] = None


def require_page_access(user, page_name):
    """
    Verifica se o usuário tem acesso à página.
    Se não tiver, exibe uma mensagem de erro e interrompe a execução.
    """
    from .page_access import has_page_access
    logger.debug("require_page_access(user, page_name)")
    if not has_page_access(user["role"], page_name):
        st.error(f"Seu perfil ({user['role']}) não tem acesso a esta página.")
        st.info("Se você acredita que isso é um erro, entre em contato com o administrador do sistema.")
        st.stop()
