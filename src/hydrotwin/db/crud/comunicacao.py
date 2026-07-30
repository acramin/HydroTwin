from datetime import datetime
from hydrotwin.helpers.logger import logger

def obter_status_comunicacao(conn):
    logger.debug("obter_status_comunicacao(conn)")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT MAX(dth_recebido)
        FROM sensor_raw
    """)

    ultima = cursor.fetchone()[0]

    if ultima is None:
        return "SEM DADOS", None

    ultima = datetime.fromisoformat(ultima)

    segundos = (
        datetime.now() - ultima
    ).total_seconds()

    if segundos > 1200:
        return "OFFLINE", ultima

    return "ONLINE", ultima