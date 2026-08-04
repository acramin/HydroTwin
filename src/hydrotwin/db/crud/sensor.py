import pandas as pd

from hydrotwin.db.conn import conectar_db
from hydrotwin.processing import analisar_tendencias, detectar_anomalias, avaliar_estado_operacional
from hydrotwin.helpers.logger import logger

### Variáveis Globais

TIPOS_ALERTA_RISCO = ("RISCO_ATENCAO", "RISCO_CRITICO")

ROTULO_METRICA = {
    "ph": "pH",
    "ec": "EC",
    "temperatura_ambiente": "Temperatura ambiente",
    "temperatura_agua": "Temperatura da água",
    "luminosidade": "Luminosidade",
    "nivel_tanque": "Nível do tanque",
    "umidade": "Umidade",
}


### Auxiliares 

def _estatisticas_dataframe(df):
    """_summary_

    Args:
        df (_type_): _description_

    Returns:
        _type_: _description_
    """
    logger.debug("_estatisticas_dataframe(df)")
    metricas = [
        "ph",
        "ec",
        "temperatura_ambiente",
        "temperatura_agua",
        "luminosidade",
        "nivel_tanque",
        "umidade",
    ]

    estatisticas = {}

    for metrica in metricas:
        serie = pd.to_numeric(df.get(metrica), errors="coerce").dropna()

        estatisticas[f"{metrica}_count"] = int(serie.count())
        estatisticas[f"{metrica}_min"] = None if serie.empty else float(serie.min())
        estatisticas[f"{metrica}_max"] = None if serie.empty else float(serie.max())
        estatisticas[f"{metrica}_mean"] = None if serie.empty else float(serie.mean())
        estatisticas[f"{metrica}_std"] = 0.0 if serie.empty else float(serie.std(ddof=0))

    return estatisticas

def _resumir_maior_contribuicao(detalhes):
    logger.debug("_resumir_maior_contribuicao(detalhes)")
    if not detalhes:
        return None

    metrica, risco = max(detalhes.items(), key=lambda item: item[1])
    nome = ROTULO_METRICA.get(metrica, metrica)
    return metrica, nome, risco

def _explicacao_da_metrica(metrica, estatisticas, cultura):
    logger.debug("_explicacao_da_metrica(metrica, estatisticas, cultura)")
    from .utils import resolver_limites
    media = estatisticas.get(f"{metrica}_mean")
    limite_min, limite_max = resolver_limites(cultura or {}, metrica)
    nome = ROTULO_METRICA.get(metrica, metrica)

    if media is None:
        return f"{nome} apresentou comportamento de risco na ultima janela analisada."

    if limite_min is not None and media < limite_min:
        return (
            f"{nome} esta abaixo do limite mínimo ({limite_min:.2f}) "
            f"com media atual de {media:.2f}."
        )

    if limite_max is not None and media > limite_max:
        return (
            f"{nome} esta acima do limite máximo ({limite_max:.2f}) "
            f"com média atual de {media:.2f}."
        )

    if limite_min is not None and limite_max is not None:
        return (
            f"{nome} esta dentro da faixa recomendada ({limite_min:.2f} a {limite_max:.2f}), "
            "mas com variação/proximidade de limite que aumentou o risco."
        )

    if limite_min is not None:
        return (
            f"{nome} esta proximo do limite mínimo recomendado ({limite_min:.2f}), "
            f"com média atual de {media:.2f}."
        )

    if limite_max is not None:
        return (
            f"{nome} esta proximo do limite máximo recomendado ({limite_max:.2f}), "
            f"com média atual de {media:.2f}."
        )

    return f"{nome} apresentou comportamento de risco na ultima janela analisada."

def _mensagem_alerta_risco(status, detalhes, estatisticas, cultura):
    logger.debug("_mensagem_alerta_risco(status, detalhes, estatisticas, cultura)")
    principal = _resumir_maior_contribuicao(detalhes)
    if principal is None:
        return None, None

    metrica_principal, nome_principal, _ = principal
    explicacao = _explicacao_da_metrica(metrica_principal, estatisticas, cultura)

    if status == "Crítico":
        mensagem = f"Risco crítico detectado em {nome_principal}. {explicacao}"
        return "RISCO_CRITICO", mensagem

    if status == "Atenção":
        mensagem = f"Atenção necessária em {nome_principal}. {explicacao}"
        return "RISCO_ATENCAO", mensagem

    return None, None

def _sincronizar_alerta_risco(cursor, bancada_id, status, detalhes, estatisticas, cultura):
    logger.debug("_sincronizar_alerta_risco(cursor, bancada_id, status, detalhes, estatisticas, cultura)")
    novo_tipo, nova_mensagem = _mensagem_alerta_risco(status, detalhes, estatisticas, cultura)

    cursor.execute(
        """
        SELECT id, tipo, mensagem
        FROM alerta
        WHERE bancada_id = ?
          AND dth_resolvido IS NULL
          AND tipo IN (?, ?)
        ORDER BY dth_criado DESC, id DESC
        """,
        (bancada_id, TIPOS_ALERTA_RISCO[0], TIPOS_ALERTA_RISCO[1]),
    )
    abertos = cursor.fetchall()

    if novo_tipo is None:
        if abertos:
            cursor.execute(
                """
                UPDATE alerta
                SET dth_resolvido = CURRENT_TIMESTAMP
                WHERE bancada_id = ?
                  AND dth_resolvido IS NULL
                  AND tipo IN (?, ?)
                """,
                (bancada_id, TIPOS_ALERTA_RISCO[0], TIPOS_ALERTA_RISCO[1]),
            )
        return

    alerta_mesmo_tipo = next((a for a in abertos if a[1] == novo_tipo), None)

    if alerta_mesmo_tipo:
        alerta_id, _, mensagem_atual = alerta_mesmo_tipo

        if mensagem_atual != nova_mensagem:
            cursor.execute(
                "UPDATE alerta SET mensagem = ? WHERE id = ?",
                (nova_mensagem, alerta_id),
            )

        for alerta_id, tipo, _ in abertos:
            if tipo != novo_tipo:
                cursor.execute(
                    "UPDATE alerta SET dth_resolvido = CURRENT_TIMESTAMP WHERE id = ?",
                    (alerta_id,),
                )
        return

    if abertos:
        cursor.execute(
            """
            UPDATE alerta
            SET dth_resolvido = CURRENT_TIMESTAMP
            WHERE bancada_id = ?
              AND dth_resolvido IS NULL
              AND tipo IN (?, ?)
            """,
            (bancada_id, TIPOS_ALERTA_RISCO[0], TIPOS_ALERTA_RISCO[1]),
        )

    cursor.execute(
        """
        INSERT INTO alerta (bancada_id, tipo, mensagem)
        VALUES (?, ?, ?)
        """,
        (bancada_id, novo_tipo, nova_mensagem),
    )

def _score_para_status(score):
    logger.debug("_score_para_status(score)")
    try:
        score_value = float(score)
    except (TypeError, ValueError):
        return "Sem dados"

    if score_value >= 100:
        return "Crítico"
    if score_value >= 50:
        return "Atenção"
    return "Saudável"

### Principais
def inserir_leitura_sensor(conn, dados: tuple) -> int:
    """
    Insere uma leitura bruta de sensor na tabela sensor_raw.
    
    Retorna o bancada_id associado ao registro.
    """
    logger.debug("inserir_leitura_sensor(conn, dados: tuple) -> int")
    import sqlite3

    if not isinstance(conn, sqlite3.Connection) :
        conn = conectar_db()
        
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO sensor_raw 
            (bancada_id, ph, ec, temperatura_ambiente, temperatura_agua, luminosidade, nivel_tanque, umidade, dth_recebido)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, dados)
        conn.commit()
        return dados[0]  # Retorna o bancada_id
    finally:
        cursor.close()

def get_raw_recent(bancada_id=None, horas=24, since=None):
    logger.debug("get_raw_recent(bancada_id=None, horas=24, since=None)")
    from datetime import datetime, timedelta

    def _query_dataframe(query, params=None):
        conn = conectar_db()
        try:
            return pd.read_sql_query(query, conn, params=params)
        finally:
            conn.close()

    filtro_bancada = ""
    filtro_since = ""
    params = []

    data_limite = (datetime.now() - timedelta(hours=horas)).strftime("%Y-%m-%d %H:%M:%S")
    params.append(data_limite)

    if since is not None:
        if hasattr(since, "strftime"):
            since_value = since.strftime("%Y-%m-%d %H:%M:%S")
        else:
            since_value = str(since)
        filtro_since = " AND dth_recebido > ?"
        params.append(since_value)

    if bancada_id is not None:
        filtro_bancada = " AND bancada_id = ?"
        params.append(bancada_id)

    query = f"""
        SELECT *
        FROM sensor_raw
        WHERE dth_recebido >= ?{filtro_since}{filtro_bancada}
        ORDER BY dth_recebido ASC
    """

    return _query_dataframe(query, params=params)

def processar_sensor(bancada_id, janela_horaria="24h", horas=24):
    logger.debug("processar_sensor(bancada_id, janela_horaria='24h', horas=24)")
    from .bancada import get_limites_bancada
    from .cultura import valor_cultura

    ultimo_proc = get_sensor_proc_ultimo(bancada_id)
    since = None if not ultimo_proc else ultimo_proc.get("dth_calculado")

    conn = conectar_db()
    try:
        cursor = conn.cursor()
        df = get_raw_recent(bancada_id=bancada_id, horas=horas, since=since)

        if df is None:
            return None

        if isinstance(df, list):
            if not df:
                logger.info("Nenhum dado novo para processar; ignorando reprocessamento.")
                return None
        elif hasattr(df, "empty") and df.empty:
            logger.info("Nenhum dado novo para processar; ignorando reprocessamento.")
            return None

        cultura = valor_cultura(cursor, bancada_id)
        estatisticas = _estatisticas_dataframe(df)
        limites_bancada = get_limites_bancada(bancada_id)
        estado_operacional = avaliar_estado_operacional(
            {
                "ph": estatisticas.get("ph_mean"),
                "ec": estatisticas.get("ec_mean"),
            },
            limites=limites_bancada,
        )
        detalhes = {
            sensor: info.get("score", 0)
            for sensor, info in (estado_operacional.get("sensores") or {}).items()
        }
        anomalia = detectar_anomalias(df)
        previsao = analisar_tendencias(df)
        consolidado = {
            "score": estado_operacional["score"],
            "status": estado_operacional["status"],
            "motivo": "Estado operacional atual baseado em pH e EC.",
        }
        n_amostras = int(df.shape[0])

        cursor.execute(
            """
            INSERT INTO sensor_proc (
                bancada_id, janela_horaria,
                ph_min, ph_max, ph_mean,
                ec_min, ec_max, ec_mean,
                temperatura_ambiente_min, temperatura_ambiente_max, temperatura_ambiente_mean,
                temperatura_agua_min, temperatura_agua_max, temperatura_agua_mean,
                luminosidade_min, luminosidade_max, luminosidade_mean,
                nivel_tanque_min, nivel_tanque_max, nivel_tanque_mean,
                umidade_min, umidade_max, umidade_mean,
                score, n_amostras,
                anomalia_score, anomalia_status,
                tendencia_score, tendencia_status,
                consolidado_score, consolidado_status, consolidado_motivo
            ) VALUES (
                ?, ?,
                ?, ?, ?,
                ?, ?, ?,
                ?, ?, ?,
                ?, ?, ?,
                ?, ?, ?,
                ?, ?, ?,
                ?, ?, ?,
                ?, ?,
                ?, ?,
                ?, ?,
                ?, ?, ?
            )
            """,
            (
                bancada_id,
                janela_horaria,
                estatisticas["ph_min"],
                estatisticas["ph_max"],
                estatisticas["ph_mean"],
                estatisticas["ec_min"],
                estatisticas["ec_max"],
                estatisticas["ec_mean"],
                estatisticas["temperatura_ambiente_min"],
                estatisticas["temperatura_ambiente_max"],
                estatisticas["temperatura_ambiente_mean"],
                estatisticas["temperatura_agua_min"],
                estatisticas["temperatura_agua_max"],
                estatisticas["temperatura_agua_mean"],
                estatisticas["luminosidade_min"],
                estatisticas["luminosidade_max"],
                estatisticas["luminosidade_mean"],
                estatisticas["nivel_tanque_min"],
                estatisticas["nivel_tanque_max"],
                estatisticas["nivel_tanque_mean"],
                estatisticas["umidade_min"],
                estatisticas["umidade_max"],
                estatisticas["umidade_mean"],
                estado_operacional["score"],
                n_amostras,
                anomalia.get("score", 0.0),
                anomalia.get("status", "Sem dados"),
                previsao.get("score", 0.0),
                previsao.get("status", "Sem previsão"),
                consolidado["score"],
                consolidado["status"],
                consolidado["motivo"],
            ),
        )

        _sincronizar_alerta_risco(
            cursor,
            bancada_id=bancada_id,
            status=estado_operacional["status"],
            detalhes=detalhes,
            estatisticas=estatisticas,
            cultura=cultura,
        )

        conn.commit()
        return {
            "score": estado_operacional["score"],
            "status": estado_operacional["status"],
            "detalhes": detalhes,
            "anomalia_score": anomalia.get("score", 0.0),
            "anomalia_status": anomalia.get("status", "Sem dados"),
            "tendencia_score": previsao.get("score", 0.0),
            "tendencia_status": previsao.get("status", "Sem previsão"),
            "consolidado_score": consolidado["score"],
            "consolidado_status": consolidado["status"],
            "consolidado_motivo": consolidado["motivo"],
            "n_amostras": n_amostras,
            "janela_horaria": janela_horaria,
        }
    finally:
        conn.close()
        
def get_sensor_proc_ultimo(bancada_id):
    logger.debug("get_sensor_proc_ultimo(bancada_id)")
    conn = conectar_db()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, bancada_id, janela_horaria, ph_min, ph_max, ph_mean,
                   ec_min, ec_max, ec_mean, temperatura_ambiente_min,
                   temperatura_ambiente_max, temperatura_ambiente_mean,
                   temperatura_agua_min, temperatura_agua_max, temperatura_agua_mean,
                   luminosidade_min, luminosidade_max, luminosidade_mean,
                   nivel_tanque_min, nivel_tanque_max, nivel_tanque_mean,
                   umidade_min, umidade_max, umidade_mean,
                 score, n_amostras, dth_calculado,
                 anomalia_score, anomalia_status,
                 tendencia_score, tendencia_status,
                 consolidado_score, consolidado_status, consolidado_motivo
            FROM sensor_proc
            WHERE bancada_id = ?
            ORDER BY dth_calculado DESC, id DESC
            LIMIT 1
            """,
            (bancada_id,),
        )
        linha = cursor.fetchone()
        if linha is None:
            return None

        colunas = [
            "id",
            "bancada_id",
            "janela_horaria",
            "ph_min",
            "ph_max",
            "ph_mean",
            "ec_min",
            "ec_max",
            "ec_mean",
            "temperatura_ambiente_min",
            "temperatura_ambiente_max",
            "temperatura_ambiente_mean",
            "temperatura_agua_min",
            "temperatura_agua_max",
            "temperatura_agua_mean",
            "luminosidade_min",
            "luminosidade_max",
            "luminosidade_mean",
            "nivel_tanque_min",
            "nivel_tanque_max",
            "nivel_tanque_mean",
            "umidade_min",
            "umidade_max",
            "umidade_mean",
            "score",
            "n_amostras",
            "dth_calculado",
            "anomalia_score",
            "anomalia_status",
            "tendencia_score",
            "tendencia_status",
            "consolidado_score",
            "consolidado_status",
            "consolidado_motivo",
        ]
        dados = dict(zip(colunas, linha))
        dados["status"] = _score_para_status(dados["score"])
        dados["status_exibicao"] = dados.get("consolidado_status")
        return dados
    finally:
        conn.close()
