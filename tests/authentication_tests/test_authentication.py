from unittest.mock import MagicMock
import pytest

# Substitua 'seu_modulo' pelo arquivo Python onde estão as suas funções
from hydrotwin.authentication import (
    PAGE_ACCESS_CONFIG,
    bootstrap_auth,
    get_access_description,
    get_allowed_pages,
    get_current_user,
    has_page_access,
    logout_user,
    require_page_access,
    set_current_user,
)


# ==============================================================================
# FIXTURES E MOCKS
# ==============================================================================

@pytest.fixture
def mock_streamlit_session(monkeypatch):
    """
    Simula o st.session_state do Streamlit como um dicionário comum
    e mocka os alertas e interrupções (st.error, st.info, st.stop).
    """
    session_store = {}
    
    # Mock do session_state
    monkeypatch.setattr("streamlit.session_state", session_store)
    
    # Mocks das funções de interface e controle
    mock_error = MagicMock()
    mock_info = MagicMock()
    
    # st.stop() no Streamlit normalmente interrompe a execução.
    # Simulamos isso lançando uma exceção personalizada durante o teste.
    def mock_stop():
        raise Exception("StreamlitStopTriggered")

    monkeypatch.setattr("streamlit.error", mock_error)
    monkeypatch.setattr("streamlit.info", mock_info)
    monkeypatch.setattr("streamlit.stop", mock_stop)

    return {
        "store": session_store,
        "error": mock_error,
        "info": mock_info,
    }


@pytest.fixture(autouse=True)
def mock_external_helpers(monkeypatch):
    """
    Isola funções de banco e helpers externos para os testes não dependerem do DB real.
    """
    monkeypatch.setattr("hydrotwin.helpers.user_session_key", lambda: "usuario_logado")
    monkeypatch.setattr("hydrotwin.db.crud.ensure_default_admin", MagicMock())
    monkeypatch.setattr("hydrotwin.helpers.get_admin_credentials", lambda: ("admin", "12345678"))
    monkeypatch.setattr("hydrotwin.helpers.is_development_mode", lambda: False)
    monkeypatch.setattr(
        "hydrotwin.db.crud.autenticar_usuario",
        MagicMock(return_value={"nome": "Admin Dev", "role": "admin"})
    )


# ==============================================================================
# TESTES DE PERMISSÕES E ROLES (PAGE ACCESS)
# ==============================================================================

class TestPageAccess:

    def test_get_allowed_pages_roles_validas(self):
        """Retorna as listas de páginas corretas para admin e viewer."""
        admin_pages = get_allowed_pages("admin")
        assert "Painel de Controle - Bancadas" in admin_pages
        assert "Simulador" in admin_pages

        viewer_pages = get_allowed_pages("viewer")
        assert "Visão Geral" in viewer_pages
        assert "Simulador" not in viewer_pages

    def test_get_allowed_pages_role_inexistente(self):
        """Retorna lista vazia para roles não cadastradas."""
        assert get_allowed_pages("inválido") == []
        assert get_allowed_pages("") == []

    @pytest.mark.parametrize(
        "role, pagina, resultado_esperado",
        [
            ("admin", "Simulador", True),
            ("admin", "Visão Geral", True),
            ("viewer", "Visão Geral", True),
            ("viewer", "Simulador", False),
            ("viewer", "Página Inexistente", False),
            ("desconhecido", "FAQ", False),
        ],
    )
    def test_has_page_access(self, role, pagina, resultado_esperado):
        """Valida a checagem booleana de acesso por role e página."""
        assert has_page_access(role, pagina) is resultado_esperado

    def test_get_access_description(self):
        """Valida se a descrição textual da role é retornada corretamente."""
        assert get_access_description("admin") == "Acesso total a todas as funcionalidades"
        assert "sem permissão" in get_access_description("viewer")
        assert get_access_description("desconhecido") == ""


# ==============================================================================
# TESTES DE SESSÃO E AUTENTICAÇÃO (STREAMLIT AUTH)
# ==============================================================================

class TestStreamlitAuth:

    def test_bootstrap_auth_producao(self, mock_streamlit_session):
        """Em modo de produção (não-DEV), inicializa a sessão como None se vazia."""
        bootstrap_auth()
        
        session = mock_streamlit_session["store"]
        assert "usuario_logado" in session
        assert session["usuario_logado"] is None

    def test_bootstrap_auth_desenvolvimento_login_automatico(self, monkeypatch, mock_streamlit_session):
        """Em modo DEV sem usuário, realiza login automático como admin."""
        monkeypatch.setattr("hydrotwin.helpers.is_development_mode", lambda: True)

        bootstrap_auth()

        session = mock_streamlit_session["store"]
        assert session["usuario_logado"] is not None
        assert session["usuario_logado"]["role"] == "admin"

    def test_bootstrap_auth_desenvolvimento_com_falha_de_autenticacao(self, monkeypatch, mock_streamlit_session):
        """Em modo DEV, se o login automático lançar exceção, silencia o erro e mantém None."""
        monkeypatch.setattr("hydrotwin.helpers.is_development_mode", lambda: True)
        monkeypatch.setattr(
            "hydrotwin.db.crud.autenticar_usuario",
            MagicMock(side_effect=Exception("Erro de conexão DB"))
        )

        bootstrap_auth()

        session = mock_streamlit_session["store"]
        assert session["usuario_logado"] is None

    def test_get_set_logout_current_user(self, mock_streamlit_session):
        """Valida o ciclo de vida completo do usuário na sessão (get, set e logout)."""
        # Inicialmente None
        assert get_current_user() is None

        # Define um usuário
        usuario_teste = {"nome": "Maria", "role": "viewer"}
        set_current_user(usuario_teste)
        assert get_current_user() == usuario_teste

        # Efetua logout
        logout_user()
        assert get_current_user() is None


# ==============================================================================
# TESTES DOGUARDRAIL DE PÁGINA (REQUIRE_PAGE_ACCESS)
# ==============================================================================

class TestRequirePageAccess:

    def test_require_page_access_permitido(self, mock_streamlit_session):
        """Não deve interromper a execução se o usuário possuir acesso à página."""
        usuario = {"nome": "Admin", "role": "admin"}
        
        # Não deve lançar exceção nem chamar st.error
        require_page_access(usuario, "Simulador")
        
        mock_streamlit_session["error"].assert_not_called()

    def test_require_page_access_negado(self, mock_streamlit_session):
        """
        Se o usuário não tiver permissão:
        1. Exibe a mensagem de erro no Streamlit.
        2. Exibe a mensagem de ajuda no Streamlit.
        3. Chama o st.stop() para parar a página.
        """
        usuario = {"nome": "João", "role": "viewer"}

        # Como nosso mock de st.stop lança "StreamlitStopTriggered", capturamos a exceção
        with pytest.raises(Exception, match="StreamlitStopTriggered"):
            require_page_access(usuario, "Simulador")

        # Verifica se as mensagens do Streamlit foram invocadas
        mock_streamlit_session["error"].assert_called_once()
        assert "Seu perfil (viewer) não tem acesso" in mock_streamlit_session["error"].call_args[0][0]
        
        mock_streamlit_session["info"].assert_called_once()