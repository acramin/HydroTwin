from hydrotwin.db.conn import conectar_db
from hydrotwin.helpers.logger import logger

# Cria todas tabelas e indexes
def create_tables():
    logger.debug("create_tables()")
    conn = conectar_db()
    cursor = conn.cursor()
    
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    # Tabela de bancada
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS bancada (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL UNIQUE,
        flag_concluido BOOLEAN NOT NULL DEFAULT 0
    );
    """)

    # Tabela de filete
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS filete (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bancada_id INTEGER NOT NULL,
        cultura_id INTEGER NOT NULL,
        data_plantio DATE NOT NULL,
        prevista_colheita DATE NOT NULL,
        flag_colhido BOOLEAN NOT NULL DEFAULT 0,
        data_colheita DATE,
        FOREIGN KEY (bancada_id) REFERENCES bancada(id),
        FOREIGN KEY (cultura_id) REFERENCES cultura(id)
    );
    """)

    # cria tabela cultura
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cultura (
        id INTEGER PRIMARY KEY,
        nome TEXT UNIQUE,
        ph_min REAL,
        ph_max REAL,
        ec_min REAL,
        ec_max REAL,
        dias_ciclo INTEGER,
        tempo_luz_acesa REAL,
        lux_min REAL,
        lux_max REAL
    )
    """)

    # Tabela de senor_raw
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sensor_raw (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bancada_id INTEGER NOT NULL,
        ph REAL,
        ec REAL,
        temperatura_ambiente REAL,
        temperatura_agua REAL,
        luminosidade REAL,
        nivel_tanque REAL,
        umidade REAL,
        dth_recebido DATETIME DEFAULT (datetime('now', '-3 hours')),
        FOREIGN KEY (bancada_id) REFERENCES bancada(id)
    );
    """)
    
    # Cria tabela de leitura processada
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sensor_proc (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bancada_id INTEGER NOT NULL,
        janela_horaria TEXT,
        ph_min REAL,
        ph_max REAL,
        ph_mean REAL,
        ec_min REAL,
        ec_max REAL,
        ec_mean REAL,
        temperatura_ambiente_min REAL,
        temperatura_ambiente_max REAL,
        temperatura_ambiente_mean REAL,
        temperatura_agua_min REAL,
        temperatura_agua_max REAL,
        temperatura_agua_mean REAL,
        luminosidade_min REAL,
        luminosidade_max REAL,
        luminosidade_mean REAL,
        nivel_tanque_min REAL,
        nivel_tanque_max REAL,
        nivel_tanque_mean REAL,
        umidade_min REAL,
        umidade_max REAL,
        umidade_mean REAL,
        score REAL,
        anomalia_score REAL,
        anomalia_status TEXT,
        tendencia_score REAL,
        tendencia_status TEXT,
        consolidado_score REAL,
        consolidado_status TEXT,
        consolidado_motivo TEXT,
        n_amostras INTEGER,
        dth_calculado DATETIME DEFAULT (datetime('now', '-3 hours')),
        FOREIGN KEY (bancada_id) REFERENCES bancada(id)
    );
    """)
    
    # Cria tabela de alertas
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS alerta (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bancada_id INTEGER NOT NULL,
        tipo TEXT,
        mensagem TEXT,
        dth_criado DATETIME DEFAULT (datetime('now', '-3 hours')),
        dth_resolvido DATETIME,
        FOREIGN KEY (bancada_id) REFERENCES bancada(id)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuario (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        role TEXT NOT NULL CHECK (role IN ('admin', 'viewer')),
        created_at DATETIME DEFAULT (datetime('now', '-3 hours'))
    );
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS convite (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT NOT NULL,
        code TEXT NOT NULL UNIQUE,
        role TEXT NOT NULL DEFAULT 'viewer' CHECK (role IN ('admin', 'viewer')),
        status TEXT NOT NULL DEFAULT 'pendente' CHECK (status IN ('pendente', 'usado', 'cancelado')),
        expires_at DATETIME NOT NULL,
        created_at DATETIME DEFAULT (datetime('now', '-3 hours'))
    );
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sessao_usuario (
        token TEXT PRIMARY KEY,
        usuario_id INTEGER NOT NULL,
        expires_at DATETIME NOT NULL,
        created_at DATETIME DEFAULT (datetime('now', '-3 hours')),
        FOREIGN KEY (usuario_id) REFERENCES usuario (id) ON DELETE CASCADE
    );               
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS controlador (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        bancada1_id INTEGER,
        bancada2_id INTEGER,
        FOREIGN KEY (bancada1_id) REFERENCES bancada(id),
        FOREIGN KEY (bancada2_id) REFERENCES bancada(id)
    );
    """)
    
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_raw_bancada_tempo ON sensor_raw(bancada_id, dth_recebido);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_raw_tempo ON sensor_raw(dth_recebido);")
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_proc_bancada_janela_tempo ON sensor_proc(bancada_id, janela_horaria, dth_calculado);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_proc_tempo_janela ON sensor_proc(janela_horaria, dth_calculado);")
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_filete_bancada ON filete(bancada_id);")
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerta_bancada_criado ON alerta(bancada_id, dth_criado);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerta_bancada_aberto ON alerta(dth_criado, dth_resolvido);")
    
    conn.commit()
    conn.close()