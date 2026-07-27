# Configuração de acesso às páginas baseado em role do usuário
# Define quais páginas cada role pode acessar

PAGE_ACCESS_CONFIG = {
    "admin": {
        "pages": [
            "Painel de Controle - Bancadas",
            "Visão Geral",
            "Monitoramento Detalhado",
            "FAQ",
            "Simulador",
        ],
        "description": "Acesso total a todas as funcionalidades"
    },
    "viewer": {
        "pages": [
            "Visão Geral",
            "Monitoramento Detalhado",
            "FAQ",
        ],
        "description": "Acesso a monitoramento e informações, sem permissão para cadastrar ou modificar dados"
    }
}

def get_allowed_pages(role: str) -> list[str]:
    """Retorna a lista de páginas permitidas para uma role"""
    config = PAGE_ACCESS_CONFIG.get(role, {})
    return config.get("pages", [])


def has_page_access(role: str, page_name: str) -> bool:
    """Verifica se uma role tem acesso a uma página específica"""
    allowed_pages = get_allowed_pages(role)
    return page_name in allowed_pages
