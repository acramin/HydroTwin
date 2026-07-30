from datetime import datetime, timedelta

from hydrotwin.db.conn import conectar_db
from hydrotwin.helpers.logger import logger

def inserir_filete(bancada_id, cultura_id, data_inicio):
    """Insere um novo filete com cultura específica"""
    logger.debug("inserir_filete(bancada_id, cultura_id, data_inicio)")
    conn = conectar_db()
    cursor = conn.cursor()
    
    # pegar ciclo da cultura
    cursor.execute("SELECT dias_ciclo FROM cultura WHERE id = ?", (cultura_id,))
    resultado = cursor.fetchone()
    ciclo = resultado[0] if resultado else None
    
    if ciclo is None:
        ciclo = 45  # valor padrão caso não esteja definido

    data_inicio_dt = datetime.strptime(data_inicio, "%Y-%m-%d")
    colheita = data_inicio_dt + timedelta(days=ciclo)

    cursor.execute("""
        INSERT INTO filete (bancada_id, cultura_id, data_plantio, prevista_colheita)
        VALUES (?, ?, ?, ?)
    """, (bancada_id, cultura_id, data_inicio, colheita.strftime("%Y-%m-%d")))
    
    filete_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return filete_id

def update_filete_colhido(filete_id, flag_colhido):
    """Atualiza o status de colhido de um filete"""
    logger.debug("update_filete_colhido(filete_id, flag_colhido)")
    conn = conectar_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE filete
        SET flag_colhido = ?, data_colheita = CASE WHEN ? = 1 THEN DATE('now') ELSE NULL END
        WHERE id = ?
    """, (flag_colhido, flag_colhido, filete_id))
    
    conn.commit()
    conn.close()
    
def get_filetes_by_bancada(bancada_id):
    """Retorna todos os filetes de uma bancada com suas informações de cultura"""
    logger.debug("get_filetes_by_bancada(bancada_id)")
    conn = conectar_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT f.id, f.bancada_id, c.id, c.nome, f.data_plantio, f.prevista_colheita, f.flag_colhido, f.data_colheita
        FROM filete f
        LEFT JOIN cultura c ON f.cultura_id = c.id
        WHERE f.bancada_id = ?
        ORDER BY f.data_plantio DESC
    """, (bancada_id,))
    
    dados = cursor.fetchall()
    conn.close()
    return dados