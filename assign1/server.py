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

# Server socket for inter-server communication.
global shipper
global harbor
    
# Log file should be global so it can be closed.
global log

def server():
    global server_socket
    global shipper
    global harbor
    global log

    server_socket = None
    shipper= None
    harbor = None
    log = None

    # If we don't get exactly 9 arguments, then we print the instructions and exit.
    #if (len(sys.argv) != 5 and len(sys.argv) != 9):
    #    print_instructions()
    #    sys.exit()

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

    '''
    Establish TCP socket for other servers to communicate with.
    ONLY IF the server overlay IP and overlay port are specified.
    '''
    if server_overlay_IP and overlayport:

        # Establish the interserver socket.
        try:
            harbor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            shipper = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            harbor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            harbor.bind((server_overlay_IP, overlayport))
            harbor.listen(5)


            socket_list.append(harbor)
            print 'server overlay started at port ' + str(overlayport)
            

            '''
            If we were given a remote overlay port, then connect to it.
            '''
            if remote_overlayport:
                try:
                    shipper.connect((server_overlay_IP, remote_overlayport))
                    socket_list.append(shipper)
                except socket.error, se0:
                    print 'TCP socket failed to connect to remote overlay. Error: ' + str(se0[0]) + ': ' + se0[1]
                    sys.exit()
        except socket.error, se1:
            print 'TCP socket bind failed. Error: ' + str(se1[0]) + ': ' + se1[1]
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

                    # Since this is the origin server, we don't need to worry about self-loops.
                    reformatted_data = 'sendto ' + destination_client + ' for ' + source_client + ' ' + str(message_text)
                    for server in socket_list:
                        print 'I GOT A MESSAGE FROM A CLIENT BUT I CANNOT LOCATE THE TARGET LOCALLY'
                        print server
                        socket_list[0].send(reformatted_data)
                        socket_list[1].send(reformatted_data)
                        #shipper.send(reformatted_data)

def remote_receive ():
    global harbor
    global log
    # Field requests forever?
    while True:
        time.sleep(1)

        ready_to_read, ready_to_write, in_error = select.select(socket_list, [], [], 0)

        '''
        # Get a connection.
        print 'remote_receive loop'
        connection, address = harbor.accept()
        print 'connection accepted'
        servers.append(connection)
        print servers
        '''

        # print ready_to_read

        for sock in ready_to_read:
            print 'iterate'

            if sock == harbor:
                new_socket, address = harbor.accept()
                new_socket.send('greet')
                print 'new socket send greet'
                print 'new socket'
                print new_socket
                print 'address'
                print address
                print 'harbor'
                print harbor

                socket_list.append(new_socket)
                print str(address) + ' connected'
            else:
                data = sock.recv(2048).strip()
                if data:
                    print "DATA:"
                    print data
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
                            print 'DOESNT EXIST HERE, FORWARDING'

                            print socket_list
                            print 'shipper'
                            print shipper
                            print 'harbor'
                            print harbor

                            for server in socket_list:
                                print 'THESE ARE MY SERVERS'
                                print server
                                # if (server != sock):
                                try:
                                    shipper.send(data)
                                    print 'shipper sent'
                                except:
                                    print 'shipper failed'
                                try:
                                    harbor.send(data)
                                    print 'harbor sent'
                                except:
                                    print 'harbor failed'
                    elif (keyword == 'greet'):
                        print 'GREET RECEIVED SOCKET WORKS' 
                else:
                    if sock in socket_list:
                        socket_list.remove(sock)

        '''
        # Check for data.
        data = connection.recv(2048).strip()
        if not data:
            break
        else:
            split_data = data.split()
            keyword = split_data[0]
            if (keyword == 'sendto'):
                destination_client = split_data[1]
                source_client = split_data[3]
                message_text = split_data[4:]

                try:
                    destination_address = username_to_socket[destination_client]
                    reformatted_data = 'recvfrom ' + source_client + ' message ' + str(message_text)
                    server_socket.sendto(reformatted_data, destination_address)
                except:
                    # Doesn't exist in this server.
                    for server in servers:
                        if (server != connection):
                            server.send(data)
        '''

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