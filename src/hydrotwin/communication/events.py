import threading
from queue import Queue
from datetime import datetime

### reader
fila_dados = Queue(maxsize=1000)

bancadas_ativas = set()
bancadas_lock = threading.Lock()

ultimo_recebimento = datetime.now()
ultimo_recebimento_lock = threading.Lock() 


### sender
fila_envio = Queue(maxsize=100)

# Dicionário para rastrear status de envios: 
# {bancada_id: {"status": "enviando|sucesso|erro", "timestamp": datetime, "mensagem": str}}
status_envios = {}
status_envios_lock = threading.Lock()

### comum
fila_confirmacao = Queue(maxsize=1000)

stop_event = threading.Event()
ready_event = threading.Event()