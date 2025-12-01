from socket import *
import os
import sys
import struct
import time
import select
import binascii

ICMP_ECHO_REQUEST = 8 # Código do tipo ICMP para Echo Request
MAX_HOPS = 30 # Número máximo de saltos 
TIMEOUT = 2.0 # Tempo limite em segundos
TRIES = 2 # Número de tentativas por salto

# FUNÇÃO DE CHECKSUM
def checksum(data): # Calcula o checksum do pacote ICMP
    csum = 0
    countTo = (len(data) // 2) * 2
    count = 0
    while count < countTo:
        thisVal = data[count + 1] * 256 + data[count]
        csum += thisVal
        csum &= 0xffffffff
        count += 2

    if countTo < len(data):
        csum += data[len(data) - 1]
        csum &= 0xffffffff

    csum = (csum >> 16) + (csum & 0xffff)
    csum += (csum >> 16)
    answer = ~csum
    answer &= 0xffff
    answer = answer >> 8 | (answer << 8 & 0xff00)
    return answer

# CONSTRÓI O PACOTE ICMP
def build_packet():
    # Header is type (8), code (8), checksum (16), id (16), sequence (16)
    myID = os.getpid() & 0xFFFF # Pega o ID do processo atual
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, 0, myID, 1) # Monta o cabeçalho com checksum 0
    data = struct.pack("d", time.time()) # Dados do pacote (timestamp)
    myChecksum = checksum(header + data) # Calcula o checksum do pacote ICMP para garantir integridade

    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, htons(myChecksum), myID, 1) # Re-monta o cabeçalho com o checksum correto
    packet = header + data # Pacote final
    return packet

# FUNÇÃO PRINCIPAL DE ROTEAMENTO
def get_route(hostname):
    timeLeft = TIMEOUT
    for ttl in range(1, MAX_HOPS): # Incrementa o TTL de 1 até o máximo definido
        for tries in range(TRIES): # Tenta enviar o pacote o número de vezes definido
            # Cria o socket raw
            mySocket = socket(AF_INET, SOCK_RAW, IPPROTO_ICMP) # Socket RAW ICMP para acesso de baixo nível

            mySocket.setsockopt(IPPROTO_IP, IP_TTL, struct.pack('I', ttl)) # Define o TTL do socket para o valor atual do loop
            mySocket.settimeout(TIMEOUT) # Define o tempo limite para o socket

            try:
                data = build_packet() # Constrói o pacote ICMP
                mySocket.sendto(data, (hostname, 0)) # Envia o pacote para o destino
                currentTime = time.time() # Marca o tempo de envio
                startedSelect = time.time() # Marca o tempo de início da espera
                whatReady = select.select([mySocket], [], [], timeLeft) # Espera até que o socket esteja pronto ou o tempo limite seja atingido
                howLongInSelect = (time.time() - startedSelect) # Calcula o tempo gasto na espera

                if whatReady[0] == []:  # Timeout
                    print(f"{ttl}\t* * * Request timed out.")

                recvPacket, addr = mySocket.recvfrom(1024) # Recebe o pacote de resposta
                timeReceived = time.time() # Marca o tempo de recebimento
                timeLeft -= howLongInSelect # Atualiza o tempo restante

                if timeLeft <= 0:
                    print(f"{ttl}\t* * * Request timed out.")

            except timeout:
                continue

            else:
                icmpHeader = recvPacket[20:28] # Extrai o cabeçalho ICMP do pacote recebido desde o byte 20 ao 28
                types, code, checksum, packetID, sequence = struct.unpack('bbHHh', icmpHeader) # Desempacota o cabeçalho ICMP
                
                if types == 11:  # Time Exceeded
                    print("ICMP Time Exceeded.")
                    bytes = struct.calcsize("d")
                    rtt = (timeReceived - currentTime) * 1000 # Calcula o RTT em milissegundos
                    # Mostra sempre o endereço IP
                    print("%d rtt=%.0f ms %s" % (ttl, rtt, addr[0])) # Imprime o TTL, RTT e endereço IP
                    # Agora tenta mostrar o nome do host:
                    try:
                        host = gethostbyaddr(addr[0])[0] # Tenta resolver o nome do host a partir do endereço IP / DNS reverso
                    except Exception:
                        host = "hostname não encontrado"
                    print("=> Hostname: %s" % host)
                elif types == 3:  # Destination Unreachable
                    print("ICMP Destination Unreachable.")
                    bytes = struct.calcsize("d")
                    rtt = (timeReceived - currentTime) * 1000
                    # Mostra sempre o endereço IP
                    print("%d rtt=%.0f ms %s" % (ttl, rtt, addr[0]))
                    # Agora tenta mostrar o nome do host:
                    try:
                        host = gethostbyaddr(addr[0])[0]
                    except Exception:
                        host = "hostname não encontrado"
                    print("=> Hostname: %s" % host)
                elif types == 0:  # Echo Reply
                    bytes = struct.calcsize("d") # Tamanho dos dados (timestamp)
                    timeSent = struct.unpack("d", recvPacket[28:28 + bytes])[0] # Extrai o timestamp do pacote recebido
                    rtt = (timeReceived - timeSent) * 1000 # Calcula o RTT em milissegundos
                    # Mostra sempre o endereço IP
                    print("%d rtt=%.0f ms %s" % (ttl, rtt, addr[0])) # Imprime o TTL, RTT e endereço IP
                    # Agora tenta mostrar o nome do host:
                    try:
                        host = gethostbyaddr(addr[0])[0] # Tenta resolver o nome do host a partir do endereço IP
                    except Exception:
                        host = "hostname não encontrado"
                    print("=> Hostname: %s" % host) # Imprime o nome do host
                    return
                else:
                    print("Error: ICMP type %d code %d" % (types, code)) 
                    return
                break
            finally:
                mySocket.close()

# REALIZA PING PARA 4 CONTINENTES DIFERENTES
if __name__ == '__main__':
    print("\n--- América do Sul ---")
    # get_route('www.google.com.br')  # Google Brasil
    get_route('www.uol.com.br')  # UOL Brasil

    # print("\n--- América do Norte ---")
    # # get_route('www.google.com')  # Google EUA
    # get_route('www.cnn.com')  # CNN EUA

    # print("\n--- Europa ---")
    # # get_route('www.google.co.uk')  # Google Reino Unido
    # get_route('www.bbc.co.uk')  # BBC Reino Unido

    # print("\n--- Ásia ---")
    # # get_route('www.google.co.in')  # Google Índia
    # get_route('www.ndtv.com')  # NDTV Índia

    # print("\n--- África ---")
    # # get_route('www.google.co.za')  # Google África do Sul
    # get_route('www.iol.co.za')  # IOL África do Sul
