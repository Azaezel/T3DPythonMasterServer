###############################################################################
#
# Torque Master Server
# --------------------
#
# Simple Master server for TGE and TGEA written in Python, free to use for
# whatever purposes you require, copy/modify or redistribute as you wish.
#
# Please give credit where it's due however.
#
# Heavily based upon the Perl master server by Thomas Lund and Push Button Master
# server by Ben Garney & Mike Kuklinski (both available on the GarageGames website)
#
# Author: Andy Rollins
#
# HISTORY
# -------
# 28/04/08 - Initial version tested and working with TGE 1.5.2 and TGEA 1.7
###############################################################################


########################   C O N F I G U R A T I O N   ########################
port = 28002               # port number to run on
buf = 4096
game_server_timeout = 180  # Number of seconds after which time a server is removed from the list
verbose = True             # If set to True displays all available information
###############################################################################


from socket import *
import struct, time
from ctypes import create_string_buffer

#######################################
def str_2_num(in_str):
    return_num = 0
    multiplier = 1
    
    for c in in_str:
        return_num += ord(chr(c)) * multiplier
        multiplier *= 256
        
    return return_num

#######################################
def num_2_str(n):
    return_string = ''
    while n > 0:
        n, b = divmod(n, 256)
        return_string += chr(b) 
    return return_string

#######################################
def num_2_2byte_str(n):
    n, b = divmod(n, 256)
    n, b1 = divmod(n, 256)    
    return chr(b) + chr(b1)

#######################################
def send_server_list(list_request):
    packet_type = chr(8)
    flag = chr(0)
    server_count = len(g_server_list)
    print('{0} {1}' .format(server_count, "Servers tracked"))
    addr = (list_request["client_ip"], list_request["client_port"])
    
    if server_count > 0:
        for index, list_item in enumerate(g_server_list):
            # Split the Ip address into seperate elements
            ip = list_item["IP"].split(".",3)

            lst_rq = int(list_request["packet_key"])
            prt=int(list_item["port"])
            response_packet= create_string_buffer(16)
            struct.pack_into("!c", response_packet, 0, bytes(packet_type, 'utf-8')) # Set to 8 for game server list query response
            struct.pack_into("!c", response_packet, 1, bytes(flag, 'utf-8')) # ??
            struct.pack_into("!i", response_packet, 2, lst_rq) # packet key used in the query made
            struct.pack_into("!c", response_packet, 3, bytes(chr(index), 'utf-8')) # packet index
            struct.pack_into("!s", response_packet, 4, bytes(str(server_count), 'utf-16')) # total number of packets
            struct.pack_into("!s", response_packet, 6, bytes(str(num_2_2byte_str(1)), 'utf-16')) # Count of how many servers there are to return
            struct.pack_into("!s", response_packet, 8, bytes(bytes(str(ip[0:3]), 'utf-8'))) # IP Address 1/4
            #struct.pack_into("!c", response_packet, 9, chr(bytes(ip[1], 'utf-8'))) # IP Address 2/4
            #struct.pack_into("!c", response_packet, 10, chr(bytes(ip[2], 'utf-8'))) # IP Address 3/4
            #struct.pack_into("!c", response_packet, 11, chr(bytes(ip[3], 'utf-8'))) # IP Address 4/4
            struct.pack_into("!i", response_packet, 12, prt)     # port number

            g_socket.sendto(response_packet, addr)

    else:
        # send back a packet to say there are no servers
        lst_rq = list_request["packet_key"]
        response_packet = struct.pack("!2c i 2c h", bytes(packet_type, 'utf-8'), bytes(flag, 'utf-8'),
                                      lst_rq, bytes('0', 'utf-8'), bytes('1', 'utf-8'), 0) 
    
        g_socket.sendto(response_packet, addr)


#######################################
def processListRequest(data):
    request_data = struct.unpack("!2ci2c", bytes(data[0:8]))
    list_request["query_flags"] = request_data[1]
    list_request["packet_key"] = request_data[2]

    # Fetch the game type which is string held in our request data
    game_type_len =  ord(request_data[4])
    pos = 8 + game_type_len
    game_type = struct.unpack("!" + str(game_type_len) + "s", bytes(data[8:pos]))
    list_request["game_type"] = game_type[0]

    # Fetch the mission type which is string held in our request data
    mission_type_len = ord(struct.unpack("c", bytes(data[pos : pos+1]))[0])
    pos += 1
    mission_type = struct.unpack("!" + str(mission_type_len) + "s", bytes(data[pos:pos+mission_type_len]))
    list_request["mission_type"] = mission_type[0]

    # Fetch the rest of the request data
    pos += mission_type_len
    request_data = struct.unpack("!2c 4s 4s 2c 2s c", bytes(data[pos:pos+15]))
    list_request["min_players"] = ord(request_data[0])
    list_request["max_players"] = ord(request_data[1])
    list_request["region_mask"] = str_2_num(request_data[2])
    list_request["version"] = str_2_num(request_data[3])
    list_request["filter_flags"] = ord(request_data[4])
    list_request["max_bots"] = ord(request_data[5])
    list_request["min_cpu"] = str_2_num(request_data[6])
    list_request["buddy_count"] = ord(request_data[7])

    # Display the information to screen
    if verbose:
        print ('{0} {1}' .format("    Game Type    : ", list_request["game_type"]))
        print ('{0} {1}' .format("    Mission Type : ", list_request["mission_type"]))
        print ('{0} {1}' .format("    Min Players  : ", list_request["min_players"]))
        print ('{0} {1}' .format("    Max Players  : ", list_request["max_players"]))
        print ('{0} {1}' .format("    Region Mask  : ", list_request["region_mask"]))
        print ('{0} {1}' .format("    Version      : ", list_request["version"]))
        print ('{0} {1}' .format("    Filter Flags : ", list_request["filter_flags"]))
        print ('{0} {1}' .format("    Max Bots     : ", list_request["max_bots"]))
        print ('{0} {1}' .format("    Min CPU      : ", list_request["min_cpu"]))
        print ('{0} {1}' .format("    Buddy Count  : ", list_request["buddy_count"]))


#######################################
def processInfoResponse(data, server_ip, server_port):

    s = findServer(server_ip, server_port)
    if s > -1:
        g_server_list[s]["last_ping"] = time.time()
    else:
        g_server_list.append( {"IP" : packet_ip, "port" : packet_port, "last_ping" : time.time() })
    
    request_data = struct.unpack("!2c 2s 2s c", data[0:7])
    flags = ord(request_data[1])
    g_server_list[s]["session"] = str_2_num(request_data[2])
    key = str_2_num(request_data[3])

    # Fetch the game type which is string held in our request data
    game_type_len =  ord(request_data[4])
    pos = 7 + game_type_len
    game_type = struct.unpack("!" + str(game_type_len) + "s", data[7:pos])
    g_server_list[s]["game_type"] = game_type[0]

    # Fetch the mission type which is string held in our request data
    mission_type_len = ord(struct.unpack("c", data[pos : pos+1])[0])
    pos = pos + 1
    mission_type = struct.unpack("!" + str(mission_type_len) + "s", data[pos:pos+mission_type_len])
    g_server_list[s]["mission_type"] = mission_type[0]

    # Fetch the rest of the request data
    pos = pos + mission_type_len
    request_data = struct.unpack("!c 4s 4s 2c 4s c", data[pos:pos+16])
    g_server_list[s]["max_players"] = ord(request_data[0])
    g_server_list[s]["region_mask"] = str_2_num(request_data[1])
    g_server_list[s]["version"] = str_2_num(request_data[2])
    g_server_list[s]["filter_flags"] = ord(request_data[3])
    g_server_list[s]["num_bots"] = ord(request_data[4])
    g_server_list[s]["cpu_speed"] = str_2_num(request_data[5])
    g_server_list[s]["num_players"] = ord(request_data[6])

    if verbose:
        print ('{0} {1}' .format("    Game type    : ", g_server_list[s]["game_type"]))
        print ('{0} {1}' .format("    Mission type : ", g_server_list[s]["mission_type"]))
        print ('{0} {1}' .format("    Number Bots  : ", g_server_list[s]["num_bots"]))
        print ('{0} {1}' .format("    Num players  : ", g_server_list[s]["num_players"]))
        
    

#######################################
def findServer( ip_address, port_no):    
    for index, list_item in enumerate(g_server_list):
        if list_item["IP"] == ip_address and list_item["port"] == port_no:
            return index
        
    return -1  
        

#######################################
def processServers():
    for index, list_item in enumerate(g_server_list):
        if list_item["last_ping"] < time.time() - game_server_timeout:
            if verbose:
                print ('{0} {1} {2} {3}' .format("Server Timed out IP:", g_server_list[index]["IP"], " Port:", g_server_list[index]["port"]))
            del g_server_list[index]


###############################################################################
## MAIN CODE BLOCK    
###############################################################################
addr = ("",port)
g_socket = socket( AF_INET, SOCK_DGRAM)
g_socket.bind(addr)

run_server = True
g_server_list = []

try:
    while run_server:

        #g_socket.settimeout(5)
        data, client = g_socket.recvfrom(buf)
        packet_ip = client[0]
        packet_port = client[1]

        processServers()    # Updates the list of servers and removes any from the list that have timed out

        out_string = struct.unpack('c', data[0:1])
        request_type = ord(out_string[0])

        if request_type == 22:    # Heartbeat from a server
            print ('{0} {1} {2} {3}' .format("Heartbeat from IP:", packet_ip, " Port:", packet_port))
            pos = findServer(packet_ip, packet_port)

            if pos > -1:
                g_server_list[pos]["last_ping"] = time.time()
            else:
                g_server_list.append( {"IP" : packet_ip, "port" : packet_port, "last_ping" : time.time() })

            # Request Information from the game server
            response_packet = struct.pack("!i", 10)
            print ('{0} {1} {2} {3}' .format("Sending Game Info Request IP:", packet_ip, " Port:", packet_port))
            g_socket.sendto(response_packet, client)
            
        elif request_type == 6:   # Game server list request
            print ('{0} {1} {2} {3}' .format("Gameserver list request from IP:", client[0], " Port:", client[1]))
            list_request = {"client_ip" : packet_ip, "client_port" : packet_port}

            processListRequest(data)
            send_server_list(list_request)

        elif request_type == 12:
            print ('{0} {1} {2} {3}' .format("Game Info response from IP: ", packet_ip, " port: ", packet_port))
            processInfoResponse(data, packet_ip, packet_port)

        elif request_type == 66:
            # Quit Server (I added this request type so I could stop the server nicely)
            # You will want to remove from a live server to stop malicious people shutting down
            # your server, either that or protect it's use via password or IP restriction.
            print ('{0}' .format("Received request to terminate server"))
            run_server = False

        else:
            print ('{0} {1}' .format("Unknown request type: ", request_type))


    print ("Server completed Successfully")        
    g_socket.close()

except:
    
    print ("FATAL ERROR OCCURRED")
    g_socket.close()
    raise









