# server.py
 
import sys
import socket
import select
import threading

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

def server():
    global server_socket
    global inter_server_socket
    print 'If we don\'t get exactly 9 arguments, then we print the instructions and exit.'
    # If we don't get exactly 9 arguments, then we print the instructions and exit.
    if (len(sys.argv) != 5 and len(sys.argv) != 9):
        print_instructions()
        sys.exit()

    print 'Parse through the arguments and determine what the port number and the log file are.'
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
    Establish UDP socket for local clients to communicate with.
    '''
    print 'Establish UDP socket for local clients to communicate with.'

    # Establish the server socket.  Also make sure the socket is reusable?
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        print 'Server socket established.'
    except socket.error, se:
        print 'Server socket failed to establish. Error: ' + str(se[0]) + ': ' + se[1]
        print 'terminating UDP server'
        sys.exit()

    # Bind the remote socket to server socket.
    try:
        listen_addr = (server_overlay_IP, port)
        server_socket.bind(listen_addr)
        print 'Server started on ' + server_overlay_IP + ' at port ' + str(port) 
    except socket.error, se:
        print 'UDP socket bind failed. Error: ' + str(se[0]) + ': ' + se[1] 
        print 'terminating UDP server'
        sys.exit()


    print 'Establish TCP socket for other servers to communicate with.'
    print 'ONLY IF the server overlay IP and overlay port are specified.'
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
            print 'Server started on ' + server_overlay_IP + ' at port ' + str(overlayport)
        except socket.error, se:
            print 'TCP socket bind failed. Error: ' + str(se[0]) + ': ' + se[1]
            print 'terminating TCP server'
            sys.exit()


    # Add the server socket to our list of clients.
    # clients.append(server_socket)

    thread_local = []
    thread_remote = []

    # Start the local receivers.
    for local_receivers in range(5):
        thread_local.append(threading.Thread(target = local_receive))
        thread_local[-1].start()

    # Start the remote receivers, again, only if we have a server overlay IP and overlay port.
    if (server_overlay_IP and overlayport):
        for remote_receivers in range(5):
            thread_remote.append(threading.Thread(target = remote_receive))
            thread_remote[-1].start()

    print '>>>>>>>> DONE <<<<<<<<<'
    # But close if the True loop ever gets broken.
    # server_socket.close()

def local_receive ():
    global server_socket
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
                welcome = 'welcome ' + client_name
                server_socket.sendto(welcome, addr)
                print client_name + ' regsitered from host ' + addr[0] + ' port ' + str(addr[1])

            # If the keyword is sendto, they are sending a direct message to a client.
            elif (keyword == 'sendto'):
                # Let's grab what we need.
                destination_client = split_data[1]
                message_text = split_data[3:]
                # We need a try catch in case the target client doesn't exist.
                try:
                    target_address = username_to_socket[destination_client]
                    source_client = socket_to_username[addr]
                    formatted_message = '[' + source_client + ']: ' + str(message_text)
                    server_socket.sendto(formatted_message, target_address)
                except:
                    print destination_client + ' not registered with server'

def remote_receive ():
    global inter_server_socketa
    # Field requests forever?
    while True:
        # Get a connection.
        connection, address = inter_server_socket.accept()

        # Check for data.
        data = connection.recv(2048).strip()
        if not data:
            print 'terminating TCP server'
            break
        else:
            print data

    connection.close()



def print_instructions ():
    print 'server [-s serveroverlayIP -o overlayport] -p portno -l logfile'
    print '\t-s <serveroverlayIP> indicates using TCP socket overlay IP'
    print '\t-o <overlayport> indicates the TCP socket overlay port'
    print '\t-p <portno> the port number for the chat server'
    print '\t-l <logfile> name of the logfile'

if __name__ == "__main__":
    print 'terminating entire server'
    sys.exit(server())