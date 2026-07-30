from hydrotwin.db.conn import conectar_db
from hydrotwin.helpers.logger import logger

def inserir_bancada(nome):
    logger.debug("inserir_bancada(nome)")
    logger.info(f"INSERT -> {repr(nome)}") # Debug
    
    """Insere uma nova bancada (sem cultura_id, que fica no filete)"""
    conn = conectar_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO bancada (nome)
        VALUES (?)
    """, (nome,))
    
    bancada_id = cursor.lastrowid

    conn.commit()
    conn.close()
    return bancada_id

def update_bancada_concluido(bancada_id, flag_concluido):
    """Atualiza o status de concluído de uma bancada"""
    logger.debug("update_bancada_concluido(bancada_id, flag_concluido)")
    conn = conectar_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE bancada
        SET flag_concluido = ?
        WHERE id = ?
    """, (flag_concluido, bancada_id))
    
    conn.commit()
    conn.close()
    
def get_bancadas():
    """Retorna lista de bancadas com seus filetes e culturas"""
    logger.debug("get_bancadas()")
    conn = conectar_db()
    cursor = conn.cursor()
    
    # Pega a bancada e o último filete com sua cultura
    cursor.execute("""
        SELECT b.id, b.nome, c.nome, f.id, f.data_plantio, f.prevista_colheita, b.flag_concluido
        FROM bancada b
        LEFT JOIN (
            SELECT f1.*
            FROM filete f1
            WHERE f1.id = (
                SELECT MAX(id) FROM filete WHERE bancada_id = f1.bancada_id
            )
        ) f ON f.bancada_id = b.id
        LEFT JOIN cultura c ON f.cultura_id = c.id
        ORDER BY b.id DESC
    """)

    dados = cursor.fetchall()
    
    conn.close()
    return dados

def get_limites_bancada(bancada_id): 
    ## usado no monitoramento detalhado e no processar
    from .utils import DEFAULT_LIMITES, resolver_limites
    from .cultura import valor_cultura
    
    logger.debug("get_limites_bancada(bancada_id)")
    
    conn = conectar_db()
    try:
        cursor = conn.cursor()
        cultura = valor_cultura(cursor, bancada_id)
        
        #logger.debug(f"Cultura: {cultura}")

        limites = {}
        for metrica in DEFAULT_LIMITES:
            limites[metrica] = resolver_limites(cultura, metrica)
            #logger.debug(f"{metrica}:{limites[metrica]}")

        return limites
    finally:
        conn.close()