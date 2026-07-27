from hydrotwin.db.conn import conectar_db

def drop_tables():
    conn = conectar_db()
    cursor = conn.cursor()
    
    cursor.execute("DROP TABLE IF EXISTS sensor_raw;")
    cursor.execute("DROP TABLE IF EXISTS filete;")
    cursor.execute("DROP TABLE IF EXISTS bancada;")
    cursor.execute("DROP TABLE IF EXISTS cultura;")
    cursor.execute("DROP TABLE IF EXISTS sensor_proc;")
    cursor.execute("DROP TABLE IF EXISTS alerta;")
    cursor.execute("DROP TABLE IF EXISTS usuario;")
    
    conn.commit()
    conn.close()