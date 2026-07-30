DEFAULT_LIMITES = {
    "ph": (5.5, 6.8),
    "ec": (0.8, 1.8),
    "temperatura_ambiente": (18.0, 26.0),
    "temperatura_agua": (10.0, 30.0),
    "luminosidade": (12000, 17000),
    "nivel_tanque": (0, 100.0),
    "umidade": (45.0, 75.0),
}

def _valor_limite_cultura(cultura, metrica, tipo):
    chave = f"{metrica}_{tipo}"
    if chave in cultura:
        return cultura.get(chave)
    return None

def resolver_limites(cultura, metrica):
    from hydrotwin.helpers.logger import logger
    
    #logger.debug(f"Resolver limites: cultura={cultura}; metrica={metrica}")
    # usa no sensor e na bancada
    limite_min = _valor_limite_cultura(cultura, metrica, "min")
    limite_max = _valor_limite_cultura(cultura, metrica, "max")

    # Usa os limites padrão somente como fallback quando não há cultura definida.
    # Se uma cultura existe, valores explícitos têm precedência e limites ausentes
    # não são preenchidos automaticamente com valores padrão.
    if not cultura:
        logger.debug(f"Usando limites padrão")
        limite_min, limite_max = DEFAULT_LIMITES.get(metrica, (None, None))

    return limite_min, limite_max
