import socket
import time
import random

clientSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Criar um socket UDP IPv4
serverAddress = ('127.0.0.1', 12001)  # Porta diferente do Ping para este serviço

try:
    while True:
        sequence_number = int(time.time())  # Usar timestamp como número de sequência
        heartbeat_message = f"Heartbeat {sequence_number} {time.strftime('%H:%M:%S', time.localtime())}"
        clientSocket.sendto(heartbeat_message.encode(), serverAddress)  # Enviar heartbeat para o servidor
        print(f"Heartbeat enviado: {heartbeat_message}")
        time.sleep(random.randint(5, 12))  # Enviar heartbeat a cada 5 a 12 segundos

except KeyboardInterrupt:
    print("Encerrando o cliente de heartbeat.")
finally:
    clientSocket.close()