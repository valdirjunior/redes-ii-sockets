from socket import *
import os
import sys
import struct
import time
import select
import binascii

ICMP_ECHO_REQUEST = 8
MAX_HOPS = 30
TIMEOUT = 2.0
TRIES = 2

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

def build_packet():
    # Header is type (8), code (8), checksum (16), id (16), sequence (16)
    myID = os.getpid() & 0xFFFF
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, 0, myID, 1)
    data = struct.pack("d", time.time())
    myChecksum = checksum(header + data)

    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, htons(myChecksum), myID, 1)
    packet = header + data
    return packet

def get_route(hostname):
    timeLeft = TIMEOUT
    for ttl in range(1, MAX_HOPS):
        for tries in range(TRIES):
            # Cria o socket raw
            mySocket = socket(AF_INET, SOCK_RAW, IPPROTO_ICMP)

            mySocket.setsockopt(IPPROTO_IP, IP_TTL, struct.pack('I', ttl))
            mySocket.settimeout(TIMEOUT)

            try:
                d = build_packet()
                mySocket.sendto(d, (hostname, 0))
                t = time.time()
                startedSelect = time.time()
                whatReady = select.select([mySocket], [], [], timeLeft)
                howLongInSelect = (time.time() - startedSelect)

                if whatReady[0] == []:  # Timeout
                    print(f"{ttl}\t* * * Request timed out.")

                recvPacket, addr = mySocket.recvfrom(1024)
                timeReceived = time.time()
                timeLeft -= howLongInSelect

                if timeLeft <= 0:
                    print(f"{ttl}\t* * * Request timed out.")

            except timeout:
                continue

            else:
                icmpHeader = recvPacket[20:28]
                types, code, checksum, packetID, sequence = struct.unpack('bbHHh', icmpHeader)
                
                if types == 11:  # Time Exceeded
                    bytes = struct.calcsize("d")
                    rtt = (timeReceived - t) * 1000
                    # Mostra sempre o endereço IP
                    print(" %d rtt=%.0f ms %s" % (ttl, rtt, addr[0]))
                    # Agora tenta mostrar o nome do host:
                    try:
                        host = gethostbyaddr(addr[0])[0]
                    except Exception:
                        host = "hostname não encontrado"
                    # Print extra: antes/depois
                    print(" => Hostname: %s" % host)
                elif types == 3:  # Destination Unreachable
                    bytes = struct.calcsize("d")
                    rtt = (timeReceived - t) * 1000
                    # Mostra sempre o endereço IP
                    print(" %d rtt=%.0f ms %s" % (ttl, rtt, addr[0]))
                    # Agora tenta mostrar o nome do host:
                    try:
                        host = gethostbyaddr(addr[0])[0]
                    except Exception:
                        host = "hostname não encontrado"
                    # Print extra: antes/depois
                    print(" => Hostname: %s" % host)
                elif types == 0:  # Echo Reply
                    bytes = struct.calcsize("d")
                    timeSent = struct.unpack("d", recvPacket[28:28 + bytes])[0]
                    rtt = (timeReceived - timeSent) * 1000
                    # Mostra sempre o endereço IP
                    print(" %d rtt=%.0f ms %s" % (ttl, rtt, addr[0]))
                    # Agora tenta mostrar o nome do host:
                    try:
                        host = gethostbyaddr(addr[0])[0]
                    except Exception:
                        host = "hostname não encontrado"
                    # Print extra: antes/depois
                    print(" => Hostname: %s" % host)
                    return
                else:
                    print("Error: ICMP type %d code %d" % (types, code))
                    return
                break
            finally:
                mySocket.close()
get_route('www.google.com')