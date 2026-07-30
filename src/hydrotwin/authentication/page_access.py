# Configuração de acesso às páginas baseado em role do usuário
# Define quais páginas cada role pode acessar

# hydrotwin/permissions.py (ou onde fica a função get_allowed_pages)

from hydrotwin import is_development_mode

PAGE_ENV_REQUIREMENTS = {
    "Simulador": ["development"], # 🔒 Apenas em ambiente de desenvolvimento
}

PAGE_ACCESS_CONFIG = {
    "admin": {
        "pages": [
            "Painel de Controle - Bancadas",
            "Visão Geral",
            "Monitoramento Detalhado",
            "FAQ",
            "Simulador",
        ],
    },
    "viewer": {
        "pages": [
            "Visão Geral",
            "Monitoramento Detalhado",
            "FAQ",
        ],
    },
}

def get_allowed_pages(role: str) -> list[str]:
    """Retorna as páginas permitidas para a role E para o ambiente atual."""
    config = PAGE_ACCESS_CONFIG.get(role, {})
    todas_paginas_role = config.get("pages", [])

    env_atual = "development" if is_development_mode() else "production"

    paginas_liberadas = []
    for pagina in todas_paginas_role:
        envs_permitidos = PAGE_ENV_REQUIREMENTS.get(pagina, ["development", "production"])
        
        # Só inclui a página se o ambiente atual for permitido
        if env_atual in envs_permitidos:
            paginas_liberadas.append(pagina)

    return paginas_liberadas


def has_page_access(role: str, page_name: str) -> bool:
    """Verifica se uma role tem acesso a uma página específica"""
    allowed_pages = get_allowed_pages(role)
    return page_name in allowed_pages
