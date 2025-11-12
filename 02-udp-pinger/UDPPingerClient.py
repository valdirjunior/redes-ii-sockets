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
    send_time = time.time() # Tempo de disparo do ping(em segundos, unix timestamp)
    label_time = time.localtime(send_time) # Converter para tempo legível

    message = f"Ping {seq} {time.strftime('%H:%M:%S', label_time)}" 

    try:
        # Enviar mensagem para o servidor
        clientSocket.sendto(message.encode(), serverAddress)

        # Receber resposta do servidor
        data, addr = clientSocket.recvfrom(1024)

        # Calcular o RTT (tempo ida e volta)
        rtt = (time.time() - send_time) * 1000 # Converter para milissegundos
        
        # Armazenar RTT para estatísticas
        rtts.append(rtt)

        print(f"Resposta: {data.decode()}")
        print(f"Tempo de ida e volta (RTT): {rtt:.3f} ms\n")

    except socket.timeout:
        print("Request timed out\n")
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
print(f"RTT mínimo: {min_rtt:.3f} ms")
print(f"RTT máximo: {max_rtt:.3f} ms")
print(f"RTT médio: {avg_rtt:.3f} ms")
print(f"Taxa de perda de pacotes: {loss_rate:.2f}%")
