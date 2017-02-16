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
    # If we don't get exactly 5 arguments, then we print the instructions and exit.
    if (len(sys.argv) != 5):
        print 'server -p portno -l logfile'
        print '\t-p <portno> the port number for the chat server'
        print '\t-l <logfile> name of the logfile'
        sys.exit()

    # Parse through the arguments and determine what the port number and the log file are.
    for index, word in enumerate(sys.argv):
        if (word[0] == '-'):
            flag = word[1].lower()
            next_word = sys.argv[index + 1]
            if (flag == 'p'):
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
        sys.exit()


    # Bind the remote socket to server socket.
    try:
        listen_addr = (host, port)
        server_socket.bind(listen_addr)
        print 'Server socket bound to host/port.'
    except socket.error, se:
        print 'Socket bind failed. Error: ' + str(se[0]) + ': ' + se[1] 
        sys.exit()

    # Add the server socket to our list of sockets.
    sockets.append(server_socket)

    # Field requests forever?
    while True:
        data, addr = server_socket.recvfrom(2048)

        if not data:
            break
        reply = 'Ok... ' + data
        server_socket.sendto(reply, addr)

        print '[' + str(addr[0]) + ':' + str(addr[1]) + '] - ' + data.strip()


    # But close if the True loop ever gets broken.
    server_socket.close()


'''
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((host, port))
    server_socket.listen(10)
 
    # Push the server socket to our list of open sockets.
    open_sockets.append(server_socket)
 
    # Print: server started on <1.2.3.4> at port <12345>...
    print "Server started on " + host + " at port " + str(port)
 
    
    while True:

        # get the list sockets which are ready to be read through select
        # 4th arg, time_out  = 0 : poll and never block
        ready_to_read, ready_to_write, in_error = select.select(open_sockets, [], [], 0)
      

        for sock in ready_to_read:
            # A client has connected.
            if sock == server_socket: 
                client_socket, address = server_socket.accept()
                open_sockets.append(client_socket)
                print "Client (%s, %s) connected" % address
                 
                broadcast(server_socket, client_socket, "[%s:%s] entered our chatting room\n" % address)
             
            # The server has received a message.
            else: 
                try:
                    # Receive data.
                    message = sock.recv(8192)
                    if message:
                        split_message = message.split()
                        keyword = split_message[0].lower()
                        if (keyword == 'register'):
                            # Put the socket and the username into the dictionaries so they can
                            # have references to each other.
                            username = split_message[1]
                            username_to_socket[username] = sock
                            socket_to_username[sock] = username
                            # Notify the client that she has been regsitered.
                            sendto(server_socket, sock, 'welcome ' + username)
                            # Broadcast to the chatroom that the client has joined & registered.
                            broadcast(server_socket, sock, "\r" + '[' + str(sock.getpeername()) + '] ' + data) 

                        elif (keyword == 'sendto'):

                            target_username = split_message[1]
                            message_text = split_message[3:]
                            if username_to_socket[target_username]:
                                sendto(server_socket, username_to_socket[target_username], message_text)
                    else:
                        # Remove the socket from the sockets list if it's not sending valid messages. 
                        # Also remove from the mappings.   
                        if sock in open_sockets:
                            open_sockets.remove(sock)
                            username = socket_to_username[sock]
                            del socket_to_username[sock]
                            del username_to_socket[username]

                        # Announce that the socket has been removed.
                        broadcast(server_socket, sock, "Client (%s, %s) is offline\n" % address) 

                # exception 
                except:
                    broadcast(server_socket, sock, "Exception thrown.")
                    broadcast(server_socket, sock, "Client (%s, %s) is offline\n" % address)
                    print sys.exc_info()
                    continue

    server_socket.close()
'''
def sendto (server_socket, target_username, message):
    '''
    if username_to_socket[target_username]:
        target_socket = username_to_socket[target_username]
        try:
            target_socket.send('[' + target_username + ']: ' + message)
        except:
            target_socket.close()
            if target_socket in open_sockets:
                open_sockets.remove(target_socket)
    '''


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
    sys.exit(server())