# client.py

import sys
import socket
import select
import threading
import time
import os

global client_name
global client_socket
global log


def client():
	global client_name
	global client_socket
	global log

	client_name = None
	client_socket = None
	log = None

	# If we don't get 9 arguments, print the instructions and exit.
	if (len(sys.argv) != 9):
		print_instructions()
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
			else:
				print_instructions()
				sys.exit()

	# Set up the log file.
	try:
		log = open(logfile, 'w')
	except:
		print 'Error opening file: ' + logfile

	# Establish the socket.
	client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	log.write('connecting to the server ' + server_IP + ' at port ' + str(port) + '\n')

	# The server's address and port.
	addr = (server_IP, port)

	# Send a registration message.
	registration = 'register ' + client_name
	log.write('sending register message ' + client_name + '\n')
	client_socket.sendto(registration, addr)

	# Loop forever.
	thread_receive = []
	thread_send = []

	# Start the receivers.
	for receivers in range(1):
		thread_receive.append(threading.Thread(target = client_receive))
		thread_receive[-1].start()
	print client_name + '# waiting for messages...'

	# Start the senders.
	for senders in range(1):
		thread_send.append(threading.Thread(target = client_send, args = (addr, )))
		thread_send[-1].start()

	# Loop forever (until exit prompt).
	while True:
		time.sleep(2)

def client_receive ():
	global client_name
	global client_socket
	global log

	while True:
		received = client_socket.recv(2048)
		if received:
			split_received = received.split()
			if not split_received:
				return
			keyword = split_received[0].lower()

			if (keyword == 'welcome'):
				print 'connected to server and registered'
				log.write('received welcome\n')
			elif (keyword == 'recvfrom'):
				source_name = split_received[1] 
				message_text = split_received[3:]
				print 'recvfrom ' + source_name + ' ' + str(message_text)  
			sys.stdout.write(client_name + '# ')
			sys.stdout.flush()
		
def client_send (address):
	global client_name
	global client_socket 

	while True:
		# Display a prompt:
		sys.stdout.write(client_name + '# ')
		sys.stdout.flush()
		user_input = sys.stdin.readline()
		perform(user_input, client_socket, address)


def perform (user_input, client_socket, address):
	global client_name, log
	# Determine what the user wants by splitting the user input and inspecting the first
	# keyword.
	split_input = user_input.split()

	if not split_input:
		return

	# If the first word is exit, then disconnect.
	keyword = split_input[0].lower()
	if (keyword == 'exit'):
		clean_up()

	# It looks like they want to send a message to someone.
	elif (keyword == 'sendto'):
		for index, word in enumerate(split_input):
			if index == 1:
				# Parse out the target of the message.
				target_client = word

		# The rest must be the text of their message.
		message_text = split_input[2:]

		# Write to file.
		log.write('sendto ' + target_client + ' ' + str(message_text))

		# Repackage the message to include sender name instead of message literal.
		repackaged_message = 'sendto ' + target_client + ' message '
		joined_message_text = ' '.join(map(str, message_text))
		combined = repackaged_message + joined_message_text

		# Send it on its merry way.
		client_socket.sendto(combined, address)

	# I have no idea what this dude is saying, let's give him some instructions.
	else: 
		print 'sendto <client\'s name> <your message>'
		return

def print_instructions ():
	print 'client -s serverIP -p portno -l logfile -n myname'
	print '\t-s <serverIP> indicates the serverIP address'
	print '\t-p <portno> indicates the server port number'
	print '\t-l <logfile> name of the logfile'
	print '\t-n <myname> indicates client name'

def print_goodbye ():
	global client_name
	# print 'exit'

def close_log ():
    global log
    if (log):
        log.write('terminating client...\n')
        log.close()


def close_sockets ():
    global client_socket
    if (client_socket):
    	client_socket.close()

def clean_up ():
	print_goodbye()
	close_log()
	close_sockets()
	os._exit(1)


def main ():
	try:
		client()
	except KeyboardInterrupt:
		clean_up()
	finally:
		clean_up()

if __name__ == "__main__":
	main()