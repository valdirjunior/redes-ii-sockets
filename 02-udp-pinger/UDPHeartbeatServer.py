import socket
import time
from threading import Thread, Lock

UDP_PORT = 12001  # Porta para o serviço de heartbeat
HEARTBEAT_TIMEOUT = 15  # Tempo em segundos para considerar a perda do heartbeat

heartbeats = {}  # Dicionário para armazenar os últimos tempos de heartbeat por cliente
lock = Lock()  # Para proteger o acesso ao dicionário de heartbeats

def cleanup_heartbeats():
    # 
    while True:
        time.sleep(5)
        with lock:
            now = time.time()

            # Remover clientes inativos do dicionário
            inactive = [ip for ip, last_time in heartbeats.items() if now - last_time > HEARTBEAT_TIMEOUT]

            # Log dos clientes inativos
            for ip in inactive:
                print(f"Cliente {ip} não enviou heartbeat nos últimos {HEARTBEAT_TIMEOUT} segundos. Considerando como perdido.")
                del heartbeats[ip]  # Remover do dicionário

# Função para o servidor de heartbeat
def servidor_heartbeat():

    # Criar socket UDP
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Atribuir endereço IP e número da porta ao socket
    serverSocket.bind(('', UDP_PORT))
    print(f"Servidor Heartbeat escutando na porta {UDP_PORT}")

    # Iniciar thread para limpeza de heartbeats inativos
    cleanup_thread = Thread(target=cleanup_heartbeats, daemon=True)
    cleanup_thread.start()

    # Loop principal para receber heartbeats
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