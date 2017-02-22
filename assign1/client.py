#!/usr/bin/env python

'''
client.py
Alan Coon
alancoon@usc.edu
'''

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

	# Parse through the arguments to find the host IP, the port number, the log file, and the client's
	# chosen username.
	flag_used = {}
	flag_used['s'] = False
	flag_used['p'] = False
	flag_used['l'] = False
	flag_used['n'] = False
	for index, word in enumerate(sys.argv):
		if (word[0] == '-'):
			flag = word[1].lower()
			try:
				next_word = sys.argv[index + 1]
				if next_word[0] == '-':
					raise
			except:
				print_instructions()
				sys.exit()
			if (flag == 's'):
				server_IP = next_word
				flag_used['s'] = True
			elif (flag == 'p'):
				try:
					port = int(next_word)
					if (port < 0 or port > 65535):
						raise
					flag_used['p'] = True
				except:
					print 'Port must be between 0 and 65535'
					sys.exit()
			elif (flag == 'l'):
				logfile = next_word
				flag_used['l'] = True
			elif (flag == 'n'):
				client_name = next_word
				flag_used['n'] = True
			else:
				print_instructions()
				sys.exit()

	valid_combination = False

	if (flag_used['s'] and flag_used['p'] and flag_used['l'] and flag_used['n']):
		valid_combination = True

	if not valid_combination:
		print_instructions()
		sys.exit()

	# Set up the log file.
	try:
		log = open('logs/' + logfile, 'w')
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
				print client_name + '# waiting for messages...'
				log.write('received welcome\n')
			elif (keyword == 'recvfrom'):
				source_name = split_received[1] 
				message_text = split_received[3:]
				print 'recvfrom ' + source_name + ' ' + ' '.join(message_text)  
				log.write('recvfrom ' + source_name + ' ' + ' '.join(message_text) + '\n')
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
		log.write('sendto ' + target_client + ' ' + ' '.join(message_text) + '\n')

		# Repackage the message to include sender name instead of message literal.
		repackaged_message = 'sendto ' + target_client + ' message '
  		joined_message_text = ' '.join(message_text)
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
		print 'exit'
		clean_up()
	finally:
		clean_up()

if __name__ == "__main__":
	main()