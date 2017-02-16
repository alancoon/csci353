# client.py

import sys
import socket
import select
import threading

global client_socket;

def client():
	global client_socket
	# If we don't get 9 arguments, print the instructions and exit.
	if (len(sys.argv) != 9):
		print 'client -s serverIP -p portno -l logfile -n myname'
		print '\t-s <serverIP> indicates the serverIP address'
		print '\t-p <portno> indicates the server port number'
		print '\t-l <logfile> name of the logfile'
		print '\t-n <myname> indicates client name'
		sys.exit()

	# Parse through the arguments to find the host IP, the port number, the log file, and the client's
	# chosen username.
	for index, word in enumerate(sys.argv):
		if (word[0] == '-'):
			flag = word[1].lower()
			next_word = sys.argv[index + 1]
			if (flag == 's'):
				server_IP = next_word
			elif (flag == 'p'):
				port = int(next_word)
			elif (flag == 'l'):
				logfile = next_word
			elif (flag == 'n'):
				client_name = next_word

	# Establish the socket.
	client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

	# The server's address and port.
	addr = (server_IP, port)

	# Send a registration message.
	registration = 'register ' + client_name
	client_socket.sendto(registration, addr)

	# Loop forever.
	thread_receive = []
	thread_send = []

	# Start the receivers.
	for receivers in range(5):
		thread_receive.append(threading.Thread(target = client_receive, args = (client_name, )))
		thread_receive[-1].start()
	print client_name + ' waiting for messages...'

	# Start the senders.
	for senders in range(1):
		thread_send.append(threading.Thread(target = client_send, args = (client_name, addr)))
		thread_send[-1].start()

	# client_socket.close()

def client_receive (client_name):
	global client_socket
	while True:
		received = client_socket.recv(2048)
		if received:
			sys.stdout.write('\n' + received)
			sys.stdout.write('[' + client_name + ']: ')
			sys.stdout.flush()

def client_send (client_name, address):
	global client_socket
	while True:
		# Display a prompt:
		sys.stdout.write('[' + client_name + ']: ')
		sys.stdout.flush()
		user_input = sys.stdin.readline()
		perform(user_input, client_socket, address)

def perform (user_input, client_socket, address):
	# Determine what the user wants by splitting the user input and inspecting the first
	# keyword.
	split_input = user_input.split()

	if not split_input:
		return

	# If the first word is exit, then disconnect.
	if (split_input[0].lower() == 'exit'):
		print '\nYou have disconnected, later.'
		#client_socket.close()
		sys.exit()

	# It looks like they want to send a message to someone.
	elif (split_input[0].lower() == 'sendto'):
		for index, word in enumerate(split_input):
			if index == 1:
				# Parse out the target of the message.
				target_client = word
			elif index == 2:
				# Did they include the 'message' part of the command?
				message_literal = word.lower()
				if (message_literal != 'message'):
					print 'sendto <client\'s name> message <your message>'
					return
		# The rest must be the text of their message.
		message_text = split_input[3:] 
		client_socket.sendto(user_input, address)

	# I have no idea what this dude is saying, let's give him some instructions.
	else: 
		print 'sendto <client\'s name> message <your message>'
		return

if __name__ == "__main__":
	sys.exit(client())