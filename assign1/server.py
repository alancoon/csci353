# server.py
 
import sys
import socket
import select
import threading
import time
import os

# List of all the other servers.
socket_list = []
# List of all the clients.
clients = []
# Translates client names to their respective socket.
username_to_socket = {}
# Translates a socket to its respective client's username.
socket_to_username = {}

# Server socket for local clients.
global server_socket

# Log file should be global so it can be closed.
global log

def server():
    global server_socket
    global log

    server_socket = None
    log = None

    '''
    # If we don't get exactly 9 arguments, then we print the instructions and exit.
    if (len(sys.argv) != 5 and len(sys.argv) != 9):
        print_instructions()
        sys.exit()
    '''
    
    # Parse through the arguments and determine what the port number and the log file are.
    server_overlay_IP = '127.0.0.1' 
    overlayport = None
    remote_overlayport = None

    for index, word in enumerate(sys.argv):
        if (word[0] == '-'):
            flag = word[1].lower()
            next_word = sys.argv[index + 1]
            if (flag == 's'):
                '''
                if (len(sys.argv) == 5):
                    print_instructions()
                    sys.exit()
                else:
                '''
                server_overlay_IP = next_word
            elif (flag == 'o'):
                '''
                if (len(sys.argv) == 5):
                    print_instructions()
                    sys.exit()
                else:
                '''
                overlayport = int(next_word)
            elif (flag == 'p'):
                port = int(next_word)
            elif (flag == 'l'):
                logfile = next_word
            elif (flag == 't'):
                remote_overlayport = int(next_word)
            else:
                print_instructions()
                sys.exit() 

    '''
    Set up the log file for I/O.
    '''
    try:
        log = open(logfile, 'w')
    except:
        print 'Error trying to open file: ' + logfile

    '''
    Establish UDP server socket for local clients to communicate with.
    '''
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    except socket.error, se:
        print 'Server socket failed to establish. Error: ' + str(se[0]) + ': ' + se[1]
        sys.exit()

    # Bind the remote socket to server socket.
    try:
        listen_addr = (server_overlay_IP, port)
        server_socket.bind(listen_addr)
        print 'server started on ' + server_overlay_IP + ' at port ' + str(port) + '...' 
        log.write('server started on ' + server_overlay_IP + ' at port ' + str(port) + '...\n')
    except socket.error, se:
        print 'UDP socket bind failed. Error: ' + str(se[0]) + ': ' + se[1] 
        sys.exit()


    # Start the local receivers.
    thread_local = threading.Thread(target = local_receive)
    thread_local.start()


    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if (server_overlay_IP and overlayport):
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((server_overlay_IP, overlayport))
        s.listen(5)


    s2 = None
    if (remote_overlayport):
        s2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s2.connect((server_overlay_IP, remote_overlayport))
        socket_list.append(s2)
        threading.Thread(target = run_remote, args = (s2, )).start()


    while True:
        conn, addr = s.accept()
        socket_list.append(conn)
        threading.Thread(target = run_remote, args = (conn, )).start()



def run_remote (sock):
    while True:
        data = sock.recv(2048)
        
        if not data:
            pass
        else:
            split_data = data.split()
            keyword = split_data[0]
            if (keyword == 'sendto'):
                destination_client = split_data[1]
                source_client = split_data[3]
                message_text = split_data[4:]
                log.write('sendto ' + destination_client + ' for ' + source_client + ' \"' + str(message_text) + '\"')
                try:
                    destination_address = username_to_socket[destination_client]
                    reformatted_data = 'recvfrom ' + source_client + ' message ' + str(message_text)
                    server_socket.sendto(reformatted_data, destination_address)
                    log.write('recvfrom ' + source_client + ' to ' + destination_client + ' \"' + str(message_text) + '\"')
                except:
                    # Doesn't exist in this server.
                    for server in socket_list:
                        if (server != sock): # Make sure we don't send back to our source.
                                             # Helps avoid self-loops.
                            print 'forwarding to ' + str(server)
                            server.send(data)

def local_receive ():
    global server_socket
    global log
    # Field requests forever?
    while True:
        data, addr = server_socket.recvfrom(2048)

        # If the data is empty then break.
        if not data:
            break
        # Otherwise we have received a message of importance... probably.
        else:
            split_data = data.split()
            # Skip over this while loop iteration if the split data is empty,
            # because it really shouldn't be as we checked if data was empty.
            if not split_data: continue
            keyword = split_data[0].lower()

            # If the keyword is register, let's add the client to the books.
            if (keyword == 'register'):
                client_name = split_data[1]
                clients.append(addr)
                username_to_socket[client_name] = addr
                socket_to_username[addr] = client_name

                # Formulate welcome response.
                welcome = 'welcome ' + client_name
                server_socket.sendto(welcome, addr)

                print client_name + ' regsitered from host ' + addr[0] + ' port ' + str(addr[1])
                log.write('received register ' + client_name + ' from host ' + addr[0] + ' port ' + str(addr[1]) + '\n')  
            # If the keyword is sendto, they are sending a direct message to a client.
            elif (keyword == 'sendto'):
                # Let's grab what we need.
                destination_client = split_data[1]
                message_text = split_data[3:]
                print socket_to_username

                # We need a try catch in case the target client doesn't exist.
                try:
                    print socket_to_username
                    print username_to_socket
                    source_client = socket_to_username[addr]
                    # Fetch address from dictionary mapping client names to addresses.
                    target_address = username_to_socket[destination_client]

                    # Write to log.
                    log.write('sendto ' + destination_client + ' for ' + source_client + ' \"' + str(message_text) + '\"\n')
                    log.write('recvfrom ' + source_client + ' to ' + destination_client + ' \"' + str(message_text) + '\"\n')

                    # Forward the data.
                    reformatted_data = 'recvfrom ' + source_client + ' message ' + str(message_text)
                    server_socket.sendto(reformatted_data, target_address)

                except:
                    # There was an issue fetching the address, writing to log, or sending the data.
                    log.write(destination_client + ' not registered with server\n')
                    log.write('sending message to server overlay \"' + str(message_text) + '\"\n')
                    source_client = socket_to_username[addr]
                    # Since this is the origin server, we don't need to worry about self-loops.
                    reformatted_data = 'sendto ' + destination_client + ' for ' + source_client + ' ' + str(message_text)
                    print 'len of socket_list ' + str(len(socket_list))
                    for server in socket_list:
                        print 'I GOT A MESSAGE FROM A CLIENT BUT I CANNOT LOCATE THE TARGET LOCALLY'
                        print server

                        server.send(reformatted_data)
                        print 'sent'



def print_instructions ():
    print 'server [-s serveroverlayIP -o overlayport] -p portno -l logfile'
    print '\t-s <serveroverlayIP> indicates using TCP socket overlay IP'
    print '\t-o <overlayport> indicates the TCP socket overlay port'
    print '\t-p <portno> the port number for the chat server'
    print '\t-l <logfile> name of the logfile'

def close_log ():
    global log
    if (log):
        log.write('terminating server...\n')
        log.close()

def close_sockets ():
    global server_socket
    global harbor
    global shipper
    if (server_socket):
        server_socket.close()
    if (harbor):
        harbor.close()
    if (shipper):
        shipper.close()

def clean_up():
    close_log()
    close_sockets()

def main ():
    try:
        server()
    except KeyboardInterrupt:
        clean_up()
        os._exit(1)

if __name__ == "__main__":
    main()