import socket
import time

# Criar um socket UDP IPv4
clientSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Definir timeout de 1 segundo para esperar as respostas
clientSocket.settimeout(1)

# Endereço do servidor UDP (localhost na porta 12000)
serverAddress = ('127.0.0.1', 12000)

# Variáveis para estatísticas
rtts = []
packets_lost = 0

for seq in range(1, 11):
    send_time = time.time()
    message = f"Ping {seq} {send_time}"

    try:
        # Enviar mensagem para o servidor
        clientSocket.sendto(message.encode(), serverAddress)

        # Receber resposta do servidor
        data, addr = clientSocket.recvfrom(1024)

        # Calcular o RTT (tempo ida e volta)
        rtt = time.time() - send_time
        
        # Armazenar RTT para estatísticas
        rtts.append(rtt)

        print(f"Resposta: {data.decode()}")
        print(f"Tempo de ida e volta (RTT): {rtt:.6f} segundos\n")

    except socket.timeout:
        print("Request timed out")
        packets_lost += 1

# Fechar o socket após o término
clientSocket.close()

# Estatísticas finais
# Se houver RTTs registrados, calcular as estatísticas
if rtts:
    min_rtt = min(rtts)
    max_rtt = max(rtts)
    avg_rtt = sum(rtts) / len(rtts)

# Senão, definir estatísticas como zero
else:
    min_rtt = max_rtt = avg_rtt = 0

loss_rate = (packets_lost / 10) * 100

print("\n***Estatísticas de Ping***")
print(f"RTT mínimo: {min_rtt:.6f} segundos")
print(f"RTT máximo: {max_rtt:.6f} segundos")
print(f"RTT médio: {avg_rtt:.6f} segundos")
print(f"Taxa de perda de pacotes: {loss_rate:.2f}%")
