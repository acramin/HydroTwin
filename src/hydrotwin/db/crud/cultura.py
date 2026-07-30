from hydrotwin.db.conn import conectar_db
from hydrotwin.helpers.logger import logger

def insert_culturas():
    conn = conectar_db()
    cursor = conn.cursor()

    culturas = [
        ('Alface', 5.5, 6.5, 0.8, 1.2, 50, 14, 12000, 17000),
        ('Agrião', 6.0, 6.8, 1.2, 1.8, 45, 14, 12000, 17000),
        ('Rúcula', 5.5, 6.5, 1.2, 1.8, 35, 14, 14000, 20000),
        ('Espinafre', 5.5, 6.6, 1.2, 1.8, 50, 14, 12000, 17000),
        ('Couve', 6.0, 7.5, 1.2, 2.0, 90, 14, 12000, 17000),
        ('Acelga', 6.0, 6.5, 1.2, 1.8, 60, 14, 12000, 17000),
        ('Escarola', 5.5, 6.5, 1.2, 1.8, 80, 14, 14000, 20000),
        ('Cebolinha', 6.0, 7.0, 1.4, 1.8, 90, 14, 12000, 17000),
        ('Manjericão', 5.5, 6.5, 1.0, 1.6, 45, 14, 12000, 17000),
        ('Coentro', 6.0, 6.7, 1.2, 1.8, 40, 14, 14000, 20000),
        ('Hortelã', 5.5, 6.5, 1.4, 1.8, 40, 14, 12000, 17000),
        ('Orégano', 6.0, 7.0, 1.2, 2.0, 60, 14, 12000, 17000),
        ('Alecrim', 5.5, 6.0, 1.0, 1.6, 90, 14, 12000, 17000),
        ('Tomilho', 5.5, 6.5, 0.8, 1.5, 40, 14, 14000, 20000),
        ('Salvia', 5.5, 6.5, 1.0, 1.6, 120, 14, 12000, 17000),
        ('Cereja', 5.5, 6.5, 2.0, 3.5, 140, 14, 12000, 17000),
        ('Morango', 5.5, 6.2, 1.0, 1.4, 90, 14, 12000, 17000),
        ('Pimentão', 5.5, 6.5, 1.8, 2.5, 120, 14, 12000, 17000),
        ('Pepino', 5.5, 6.5, 1.7, 2.5, 70, 14, 12000, 17000),
    ]

    for cultura in culturas:
        cursor.execute("""
        INSERT OR IGNORE INTO cultura (nome, ph_min, ph_max, ec_min, ec_max, dias_ciclo, tempo_luz_acesa, lux_min, lux_max)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, cultura)
        
    conn.commit()
    conn.close()

def get_culturas():
    conn = conectar_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, nome, dias_ciclo FROM cultura")
    dados = cursor.fetchall()
    
    conn.commit()
    conn.close()
    return dados

## esse é pela bancada
def valor_cultura(cursor, bancada_id):
    # usado no get_limites_bancada e no processador
    """Retorna os parâmetros da cultura do filete mais recente da bancada"""
    cursor.execute(
        """
        SELECT c.id, c.nome, c.ph_min, c.ph_max, c.ec_min, c.ec_max, c.dias_ciclo, tempo_luz_acesa, lux_min, lux_max
        FROM filete f
        LEFT JOIN cultura c ON c.id = f.cultura_id
        WHERE f.bancada_id = ?
        ORDER BY f.id DESC
        LIMIT 1
        """,
        (bancada_id,),
    )
    linha = cursor.fetchone()

    if not linha or linha[0] is None:
        logger.debug(f"Retorno vazio. Usar valores padrão para avaliações.")
        return {}

    return {
        "id": linha[0],
        "nome": linha[1],
        "ph_min": linha[2],
        "ph_max": linha[3],
        "ec_min": linha[4],
        "ec_max": linha[5],
        "dias_ciclo": linha[6],
        "tempo_luz_acesa": linha[7],
        "lux_min": linha[8], 
        "lux_max": linha[9]
    }

## esse é pela cultura mesmo - usado no sender  
def obter_parametros_cultura(cultura_id: int) -> dict | None:
    """Retorna os parâmetros ideais de uma cultura a partir do banco de dados."""
    conn = conectar_db()
    if not conn:
        logger.error("Não foi possível conectar ao banco de dados para buscar parâmetros.")
        return None

    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, nome, ph_min, ph_max, ec_min, ec_max, dias_ciclo, tempo_luz_acesa, lux_min, lux_max
            FROM cultura
            WHERE id = ?
        """, (cultura_id,))
        
        resultado = cursor.fetchone()
        cursor.close()

        if not resultado:
            return None

        return {
            "cultura_id": resultado[0],
            "nome": resultado[1],
            "ph_min": resultado[2],
            "ph_max": resultado[3],
            "ec_min": resultado[4],
            "ec_max": resultado[5],
            "dias_ciclo": resultado[6],
            "tempo_luz_acesa" : resultado[7],
            "lux_min" : resultado[8],
            "lux_max" : resultado[9]
        }
    except Exception as e:
        logger.error(f"Erro ao buscar cultura {cultura_id} no banco: {e}")
        return None
    finally:
        conn.close()