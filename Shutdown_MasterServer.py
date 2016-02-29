#########################################
#
# Simple script to send a shutdown signal
# to the master server, packet type 66
#
#########################################

from socket import *
import struct
host = "localhost"
port = 21567
buf = 1024
addr = (host,port)

UDPSock = socket (AF_INET, SOCK_DGRAM)

data = struct.pack("!c",chr(66))
UDPSock.sendto(data,addr)
UDPSock.close()