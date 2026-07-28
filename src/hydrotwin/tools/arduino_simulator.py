import argparse
import random
import socket
import sys
import threading
import time

# ================= CONFIGURAÇÃO PADRÃO =================
HOST = '127.0.0.1'
PORT = 65432
INTERVALO_GERACAO_S = 2

# BANCADAS SIMULADAS
BANCADAS_IDS = [1, 2, 3]

# ================= ESTADO SIMULADO DA FÍSICA =================
estado_bancadas = {}
estado_lock = threading.Lock()
socket_send_lock = threading.Lock()
stop_event = threading.Event()


def _inicializar_estado():
    return {
        "ph": random.uniform(5.8, 6.2),
        "ec": random.uniform(1.0, 1.5),
        "temp_ar": random.uniform(20, 26),
        "temp_agua": random.uniform(18, 24),
        "luz": random.uniform(10, 14),
        "nivel": random.uniform(0, 100),
        "umidade": random.uniform(55, 65),
        "bomba_ligada": True
    }


def _atualizar_estado(estado):
    def drift(valor, variacao, minimo, maximo):
        valor += random.uniform(-variacao, variacao)
        return max(min(valor, maximo), minimo)

    estado["ph"] = drift(estado["ph"], 0.02, 5.5, 6.5)
    estado["ec"] = drift(estado["ec"], 0.05, 0.5, 2.5)
    estado["temp_ar"] = drift(estado["temp_ar"], 0.2, 15, 30)
    estado["temp_agua"] += (estado["temp_ar"] - estado["temp_agua"]) * 0.05
    estado["luz"] = drift(estado["luz"], 0.5, 8, 16)
    estado["umidade"] = drift(estado["umidade"], 0.5, 40, 90)

    if random.random() < 0.001:
        estado["bomba_ligada"] = not estado["bomba_ligada"]

    if estado["bomba_ligada"]:
        estado["nivel"] = 100
    else:
        estado["nivel"] = 0

    return estado


def gerar_linha_telemetria(bancada_id: int) -> str:
    """Gera linha exatamente no formato esperado pelo Reader:
    B{id},{ph},{ec},{temp_ambiente},{temp_agua},{luminosidade},{nivel_tanque},{umidade}\n
    """
    with estado_lock:
        if bancada_id not in estado_bancadas:
            estado_bancadas[bancada_id] = _inicializar_estado()
        st = _atualizar_estado(estado_bancadas[bancada_id])

    return (
        f"B{bancada_id},"
        f"{st['ph']:.2f},"
        f"{st['ec']:.2f},"
        f"{st['temp_ar']:.2f},"
        f"{st['temp_agua']:.2f},"
        f"{st['luz']:.2f},"
        f"{st['nivel']:.2f},"
        f"{st['umidade']:.2f}\n"
    )


def safe_send(sock: socket.socket, mensagem: str):
    """Garante envio thread-safe e trata sockets fechados."""
    with socket_send_lock:
        if stop_event.is_set():
            return
        try:
            sock.sendall(mensagem.encode('utf-8'))
        except (OSError, BrokenPipeError):
            stop_event.set()


# ================= WORKER 1: ENVIO DE TELEMETRIA =================
def worker_telemetria(sock: socket.socket):
    print("📡 [TELEMETRIA] Worker de envio iniciado.")
    while not stop_event.is_set():
        for b_id in BANCADAS_IDS:
            if stop_event.is_set():
                break

            linha = gerar_linha_telemetria(b_id)
            try:
                safe_send(sock, linha)
                print(f"📡 [TELEMETRIA] Enviado: {linha.strip()}")
            except Exception as e:
                print(f"❌ [TELEMETRIA] Erro de envio: {e}")
                stop_event.set()
                return

        stop_event.wait(INTERVALO_GERACAO_S)


# ================= WORKER 2: ESCUTA E RESPOSTA DE COMANDOS =================
def worker_comandos(sock: socket.socket, behavior: str):
    print(f"⚙️ [COMANDOS] Worker de resposta iniciado (Modo: {behavior.upper()})")
    buffer = ""

    while not stop_event.is_set():
        try:
            data = sock.recv(1024)
            if not data:
                print("⚠️ [COMANDOS] Conexão encerrada pelo Manager.")
                stop_event.set()
                break

            buffer += data.decode('utf-8')

            # Processa linha a linha (Framing TCP)
            while "\n" in buffer:
                linha, buffer = buffer.split("\n", 1)
                linha = linha.strip()
                if not linha:
                    continue

                print(f"📩 [COMANDOS] Recebido do Manager: {linha}")

                # Processa comandos no formato PARAMS,bancada_id=X,...
                if linha.startswith("PARAMS"):
                    processar_comando(sock, linha, behavior)

        except (ConnectionResetError, OSError):
            print("⚠️ [COMANDOS] Conexão perdida com o Manager.")
            stop_event.set()
            break


def processar_comando(sock: socket.socket, linha: str, behavior: str):
    campos = {}
    partes = linha.split(",")
    for p in partes[1:]:
        if "=" in p:
            k, v = p.split("=", 1)
            campos[k.strip()] = v.strip()

    bancada_id = campos.get("bancada_id", "1")

    # Injeção de comportamentos para teste de resiliência
    if behavior == "normal":
        resposta = f"PARAMS_OK,bancada_id={bancada_id}\n"
        safe_send(sock, resposta)
        print(f"✅ [COMANDOS] Respondido: {resposta.strip()}")

    elif behavior == "erro":
        resposta = f"PARAMS_ERROR,bancada_id={bancada_id},motivo=Sensores fora do limite de calibração\n"
        safe_send(sock, resposta)
        print(f"⚠️ [COMANDOS] Respondido Erro: {resposta.strip()}")

    elif behavior == "atrasado":
        print("⏳ [COMANDOS] Simulando atraso no hardware (11 segundos para estourar timeout)...")
        time.sleep(11)
        resposta = f"PARAMS_OK,bancada_id={bancada_id}\n"
        try:
            safe_send(sock, resposta)
            print(f"✅ [COMANDOS] Respondido com atraso: {resposta.strip()}")
        except Exception:
            pass

    elif behavior == "sem_resposta":
        print("🤐 [COMANDOS] Ignorando comando (simulando timeout no Manager)...")

    elif behavior == "desconectar":
        print("💥 [COMANDOS] Simulando queda de conexão do hardware...")
        sock.close()
        stop_event.set()


# ================= MAIN & CLI =================
def main():
    parser = argparse.ArgumentParser(description="Simulador Integrado HydroTwin")
    parser.add_argument("--host", default=HOST, help="IP do Manager")
    parser.add_argument("--port", type=int, default=PORT, help="Porta do Manager")
    parser.add_argument(
        "--mode",
        choices=["full", "send", "receive"],
        default="full",
        help="full: Telemetria + Resposta | send: Apenas Telemetria | receive: Apenas Resposta de Comandos"
    )
    parser.add_argument(
        "--behavior",
        choices=["normal", "erro", "atrasado", "sem_resposta", "desconectar"],
        default="normal",
        help="Comportamento do simulador ao receber comandos PARAMS do Sender"
    )

    args = parser.parse_args()

    # Conexão TCP com retry
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print(f"🔌 Conectando ao Manager em {args.host}:{args.port}...")
    
    conectado = False
    for i in range(1, 6):
        try:
            sock.connect((args.host, args.port))
            conectado = True
            print("🚀 Conectado com sucesso!")
            break
        except Exception as e:
            print(f"Tentativa {i}/5 falhou ({e}). Aguardando 2s...")
            time.sleep(2)

    if not conectado:
        print("❌ Não foi possível conectar ao Manager. Suba o manager.py primeiro!")
        sys.exit(1)

    threads = []

    # Inicia threads com base no modo escolhido
    if args.mode in ["full", "receive"]:
        t_cmd = threading.Thread(
            target=worker_comandos, 
            args=(sock, args.behavior), 
            daemon=True
        )
        t_cmd.start()
        threads.append(t_cmd)

    if args.mode in ["full", "send"]:
        t_tele = threading.Thread(
            target=worker_telemetria, 
            args=(sock,), 
            daemon=True
        )
        t_tele.start()
        threads.append(t_tele)

    try:
        while not stop_event.is_set():
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n🛑 Encerrando simulador...")
    finally:
        stop_event.set()
        try:
            sock.close()
        except Exception:
            pass
        print("Simulador finalizado.")


if __name__ == "__main__":
    main()