from socket import *
import os
import sys
import struct
import time
import select
import socket

ICMP_ECHO_REQUEST = 8


def get_my_ip():
    auxSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        auxSocket.connect(('8.8.8.8', 80))
        ip = auxSocket.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        auxSocket.close()
    return ip

def create_false_ip():
    my_ip = get_my_ip()
    print('Meu IP: ', my_ip)
    # monte um IP "falso" variando o último octeto
    ip_parts = my_ip.split('.')
    false_ip = '.'.join(ip_parts[:-1]+['254'])  # se não estiver em uso
    print('IP falso: ', false_ip)
    return false_ip



def checksum(data):
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

# RECEBE UM PACOTE ICMP
def receiveOnePing(mySocket, ID, timeout, destAddr):
    timeLeft = timeout

    while 1:
        startedSelect = time.time()
        whatReady = select.select([mySocket], [], [], timeLeft)
        howLongInSelect = (time.time() - startedSelect)
        if whatReady[0] == []: # Timeout
            return None, "Request timed out."
        
        timeReceived = time.time()
        recPacket, addr = mySocket.recvfrom(1024)

        icmpHeader = recPacket[20:28]
        type, code, checksum, packetID, sequence = struct.unpack("bbHHh", icmpHeader)
        if type == 0 and packetID == ID:  # Echo Reply
            timeSent = struct.unpack("d", recPacket[28:36])[0]
            rtt = (timeReceived - timeSent) * 1000
            return rtt, None
        elif type == 3:  # Destination Unreachable
            if code == 0:
                return None, 'Rede inatingível'
            elif code == 1:
                return None, 'Host inatingível'
            elif code == 2:
                return None, 'Protocolo inatingível'
            elif code == 3:
                return None, 'Porta inatingível'
            elif code == 9:
                return None, 'Rede proibida por política/ACL'
            elif code == 10:
                return None, 'Host proibido por política/ACL'
            else:
                return None, f'ICMP Destination Unreachable, código: {code}'

        
        timeLeft -= howLongInSelect
        if timeLeft <= 0:
            return None, "Request timed out."

# ENVIA UM PACOTE DE ECHO REQUEST
def sendOnePing(mySocket, destAddr, ID):
    # Header is type (8), code (8), checksum (16), id (16), sequence (16)
    myChecksum = 0 

    # Make a dummy header with a 0 checksum
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)
    data = struct.pack("d", time.time())
    
    # Calculate the checksum on the data and the dummy header.
    myChecksum = checksum(header + data)

    # Get the right checksum, and put in the header
    if sys.platform == 'darwin':
        myChecksum = htons(myChecksum) & 0xffff
    else:
        myChecksum = htons(myChecksum)

    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)
    packet = header + data

    mySocket.sendto(packet, (destAddr, 1)) # AF_INET address must be tuple, not str

def doOnePing(destAddr, timeout):
    icmp = getprotobyname("icmp")
    mySocket = socket.socket(socket.AF_INET, socket.SOCK_RAW, icmp)

    myID = os.getpid() & 0xFFFF # Return the current process id
    sendOnePing(mySocket, destAddr, myID)
    result = receiveOnePing(mySocket, myID, timeout, destAddr)
    
    mySocket.close()
    return result

# FUNÇÃO PRINCIPAL – ESTATÍSTICAS

def ping(host, timeout=1, count=4):
    dest = gethostbyname(host)
    print(f'Pingando {dest} usando Python:')
    rtts = []
    perdas = 0
    for i in range(count):
        rtt, error = doOnePing(dest, timeout)
        if rtt is not None:
            print(f'Resposta de {dest}: time={rtt:.2f}ms')
            rtts.append(rtt)
        else:
            print(f'Falha: {error}')
            perdas += 1
        time.sleep(1)
    print('\n--- Estatísticas ---')
    if rtts:
        print(f'Mínimo RTT: {min(rtts):.2f}ms')
        print(f'Máximo RTT: {max(rtts):.2f}ms')
        print(f'Médio RTT: {sum(rtts)/len(rtts):.2f}ms')
    print(f'Taxa de perda: {perdas/count*100:.1f}%\n')

if __name__ == "__main__":
    print("--- Localhost ---")
    ping('127.0.0.1')

    print("--- América do Sul ---")
    ping('168.197.252.10')

    print("\n--- América do Norte ---")
    ping('8.8.8.8')

    print("\n--- Europa ---")
    ping('1.1.1.1')

    print("\n--- Ásia ---")
    ping('210.129.145.150')

    print("\n--- África ---")
    ping('196.10.53.74')

    print("\n--- IP Falso ---")
    ping(false_ip := create_false_ip())

