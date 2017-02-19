# server.py
 
import sys
import socket
import select
import threading
import time
import os

# List of all the other servers.
servers = []
# List of all the clients.
clients = []
# Translates client names to their respective socket.
username_to_socket = {}
# Translates a socket to its respective client's username.
socket_to_username = {}

# Server socket for local clients.
global server_socket

# Server socket for inter-server communication.
global inter_server_socket
    
# Log file should be global so it can be closed.
global log

def server():
    global server_socket
    global inter_server_socket
    global log

    server_socket = None
    inter_server_socket= None
    log = None

    # If we don't get exactly 9 arguments, then we print the instructions and exit.
    if (len(sys.argv) != 5 and len(sys.argv) != 9):
        print_instructions()
        sys.exit()

    # Parse through the arguments and determine what the port number and the log file are.
    server_overlay_IP = '127.0.0.1' 
    overlayport = None
    for index, word in enumerate(sys.argv):
        if (word[0] == '-'):
            flag = word[1].lower()
            next_word = sys.argv[index + 1]
            if (flag == 's'):
                if (len(sys.argv) == 5):
                    print_instructions()
                    sys.exit()
                else:
                    server_overlay_IP = next_word
            elif (flag == 'o'):
                if (len(sys.argv) == 5):
                    print_instructions()
                    sys.exit()
                else:
                    overlayport = int(next_word)
            elif (flag == 'p'):
                port = int(next_word)
            elif (flag == 'l'):
                logfile = next_word
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

    '''
    Establish TCP socket for other servers to communicate with.
    ONLY IF the server overlay IP and overlay port are specified.
    '''
    if server_overlay_IP and overlayport:

        # Establish the interserver socket.
        try:
            inter_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            inter_server_socket.bind((server_overlay_IP, overlayport))
            inter_server_socket.listen(5)
            print 'server overlay started at port ' + str(overlayport)
            
        except socket.error, se:
            print 'TCP socket bind failed. Error: ' + str(se[0]) + ': ' + se[1]
            sys.exit()

    thread_local = []
    thread_remote = []

    # Start the local receivers.
    for local_receivers in range(1):
        thread_local.append(threading.Thread(target = local_receive))
        thread_local[-1].start()

    # Start the remote receivers, again, only if we have a server overlay IP and overlay port.
    if (server_overlay_IP and overlayport):
        for remote_receivers in range(1):
            thread_remote.append(threading.Thread(target = remote_receive))
            thread_remote[-1].start()

    # Loop forever (until keyboard interrupt).
    while True:
        time.sleep(2)

def local_receive ():
    global server_socket
    global log
    # Field requests forever?
    while True:
        data, addr = server_socket.recvfrom(2048)

        # If the data is empty then break.
        if not data:
            print 'terminating UDP server'
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
                print '<DEBUG> SENDTO RECEIVED'
                # Let's grab what we need.
                destination_client = split_data[1]
                source_client = split_data[2]
                message_text = split_data[3:]

                print data
                print destination_client
                print source_client
                print message_text

                print username_to_socket
                print socket_to_username


                target_address = username_to_socket[destination_client]
                # We need a try catch in case the target client doesn't exist.
                try:
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

                    for server in servers:
                        server.send(data)

def remote_receive ():
    global inter_server_socket
    global log
    # Field requests forever?
    while True:
        # Get a connection.
        print 'remote_receive loop'
        connection, address = inter_server_socket.accept()
        print 'connection accepted'
        servers.append(connection)
        print servers

        # Check for data.
        data = connection.recv(2048).strip()
        if not data:
            break
        else:
            print data

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
    global inter_server_socket
    if (server_socket):
        server_socket.close()
    if (inter_server_socket):
        inter_server_socket.close()

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