# server.py
 
import sys
import socket
import select

# Host...?
host = '' 
# List of all the sockets.
sockets = []
# Translates client names to their respective socket.
username_to_socket = {}
# Translates a socket to its respective client's username.
socket_to_username = {}

def server():
    # If we don't get exactly 9 arguments, then we print the instructions and exit.
    if (len(sys.argv) != 9):
        print 'server -s serveroverlayIP -o overlayport -p portno -l logfile'
        print '\t-s <serveroverlayIP> indicates using TCP socket overlay IP'
        print '\t-o <overlayport> indicates the TCP socket overlay port'
        print '\t-p <portno> the port number for the chat server'
        print '\t-l <logfile> name of the logfile'
        sys.exit()

    # Parse through the arguments and determine what the port number and the log file are.
    for index, word in enumerate(sys.argv):
        if (word[0] == '-'):
            flag = word[1].lower()
            next_word = sys.argv[index + 1]
            if (flag == 's'):
                server_overlay_IP

            elif (flag == 'p'):
                port = int(next_word)
            elif (flag == 'l'):
                logfile = next_word

    # Establish the server socket.  Also make sure the socket is reusable?
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        print 'Server socket established.'
    except socket.error, se:
        print 'Server socket failed to establish. Error: ' + str(se[0]) + ': ' + se[1]
        print 'terminating server'
        sys.exit()

    # Bind the remote socket to server socket.
    try:
        listen_addr = (host, port)
        server_socket.bind(listen_addr)
        print 'Server started on ' + '127.0.0.1' + ' at port ' + str(port) 
    except socket.error, se:
        print 'Socket bind failed. Error: ' + str(se[0]) + ': ' + se[1] 
        print 'terminating server'
        sys.exit()

    # Add the server socket to our list of sockets.
    sockets.append(server_socket)

    # Field requests forever?
    while True:
        data, addr = server_socket.recvfrom(2048)

        # If the data is empty then break.
        if not data:
            print 'terminating server'
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
                sockets.append(addr)
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

            

    # But close if the True loop ever gets broken.
    server_socket.close()





# broadcast chat messages to all connected clients
def broadcast (server_socket, sock, message):
    '''
    for socket in open_sockets:
        # send the message only to peer
        if socket != server_socket and socket != sock :
            try :
                socket.send(message)
            except :
                # broken socket connection
                socket.close()
                # broken socket, remove it
                if socket in open_sockets:
                    open_sockets.remove(socket)
    '''


if __name__ == "__main__":
    print 'terminating server'
    sys.exit(server())