from hydrotwin.db.conn import conectar_db
from hydrotwin.helpers.logger import logger

def criar_controlador(name: str, bancada1_id: int = None, bancada2_id: int = None) -> int:
    with conectar_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO controlador (name, bancada1_id, bancada2_id)
            VALUES (?, ?, ?)
        """, (name, bancada1_id, bancada2_id))
        return cursor.lastrowid


def obter_controladores_com_vagas():
    """Retorna os controladores que têm ao menos uma bancada livre."""
    with conectar_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, bancada1_id, bancada2_id
            FROM controlador
            WHERE bancada1_id IS NULL OR bancada2_id IS NULL
        """)
        logger.debug(f"Obtendo controladores com vaga.")
        return cursor.fetchall()


def associar_bancada_ao_controlador(controlador_id: int, bancada_id: int):
    """Associa a bancada criada ao primeiro slot vago (bancada1_id ou bancada2_id)."""
    with conectar_db() as conn:
        cursor = conn.cursor()
        # Verifica qual slot está livre
        cursor.execute("SELECT bancada1_id, bancada2_id FROM controlador WHERE id = ?", (controlador_id,))
        ctrl = cursor.fetchone()
        
        if ctrl:
            b1, b2 = ctrl
            if b1 is None:
                cursor.execute("UPDATE controlador SET bancada1_id = ? WHERE id = ?", (bancada_id, controlador_id))
                logger.debug(f"Associando primeira bancada.")
            elif b2 is None:
                cursor.execute("UPDATE controlador SET bancada2_id = ? WHERE id = ?", (bancada_id, controlador_id))
                logger.debug(f"Associando segunda bancada.")

def get_controladores():
    """Retorna todos os controladores cadastrados."""
    with conectar_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, bancada1_id, bancada2_id FROM controlador")
        logger.debug(f"Obtendo controladores e associações.")
        return cursor.fetchall()
