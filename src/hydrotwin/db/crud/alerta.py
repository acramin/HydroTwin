from hydrotwin.db.conn import conectar_db

def get_alertas_ativos(bancada_id=None):
    conn = conectar_db()
    try:
        cursor = conn.cursor()

        filtro_bancada = ""
        params = []

        if bancada_id is not None:
            filtro_bancada = " AND a.bancada_id = ?"
            params.append(bancada_id)

        cursor.execute(
            f"""
            SELECT a.id, a.bancada_id, b.nome, a.tipo, a.mensagem, a.dth_criado
            FROM alerta a
            JOIN bancada b ON b.id = a.bancada_id
            WHERE a.dth_resolvido IS NULL{filtro_bancada}
            ORDER BY a.dth_criado DESC, a.id DESC
            """,
            params,
        )

        colunas = ["id", "bancada_id", "bancada_nome", "tipo", "mensagem", "dth_criado"]
        return [dict(zip(colunas, linha)) for linha in cursor.fetchall()]
    finally:
        conn.close()
