import socket
import time
from threading import Thread, Lock

UDP_PORT = 12001  # Porta para o serviço de heartbeat
HEARTBEAT_TIMEOUT = 15  # Tempo em segundos para considerar oa perda do heartbeat

heartbeats = {}
lock = Lock()

def cleanup_heartbeats():
    while True:
        time.sleep(5)
        with lock:
            now = time.time()
            inactive = [ip for ip, last_time in heartbeats.items() if now - last_time > HEARTBEAT_TIMEOUT]
            for ip in inactive:
                print(f"Cliente {ip} não enviou heartbeat nos últimos {HEARTBEAT_TIMEOUT} segundos. Considerando como perdido.")
                del heartbeats[ip]

def servidor_heartbeat():
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    serverSocket.bind(('', UDP_PORT))
    print(f"Servidor Heartbeat escutando na porta {UDP_PORT}")

    cleanup_thread = Thread(target=cleanup_heartbeats, daemon=True)
    cleanup_thread.start()

    while True:
        data, addr = serverSocket.recvfrom(1024)
        message = data.decode()
        with lock:
            heartbeats[addr[0]] = time.time()
        print(f"Recebido heartbeat de {addr[0]}: {message}")

try:
    servidor_heartbeat()
except KeyboardInterrupt:
    print("Servidor Heartbeat finalizado.")