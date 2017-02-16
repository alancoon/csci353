# client.py

import sys
import socket
import select
 
def client():
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
				serverIP = next_word
				print 'serverIP', serverIP
			elif (flag == 'p'):
				port_string = next_word
				port = int(port_string)
				print 'port_string', port_string
			elif (flag == 'l'):
				logfile = next_word
				print 'logfile', logfile
			elif (flag == 'n'):
				client_name = next_word
				print 'client_name', client_name

	# Establish the socket.
	client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	 
	# Attempt connection on the established socket.
	try :
		client_socket.connect((serverIP, port))
		register_message = 'register ' + client_name
		client_socket.send(register_message);
	except:
		print 'Failure to connect.'
		sys.exit()

	# We have connected.
	print 'Connected to remote host. You can start sending messages'  
	sys.stdout.write('[' + client_name + ']: ')
	sys.stdout.flush()
	 
	while True:
		socket_list = [sys.stdin, client_socket]
		 
		# Get the list sockets which are readable
		ready_to_read,ready_to_write,in_error = select.select(socket_list , [], [])
		 
		for sock in ready_to_read:             
			if sock == client_socket:
				message = sock.recv(4096)
				if message:
					# Parse the received message.


					# Print the message's text.
					sys.stdout.write(message)
					# Display the input prompt.
					sys.stdout.write('[' + client_name + ']: ');
					sys.stdout.flush()
				else:
					print 'nothing there'
					#print '\nConnection dropped!'
					#sys.exit()
			else :
				# Sending a message.
				message = sys.stdin.readline()
				# Determine what the user wants by splitting the message and inspecting the first
				# keyword.
				split_message = message.split()

				# If the first word is exit, then disconnect.
				if (split_message[0].lower() == 'exit'):
					print '\nYou have disconnected! Goodbye.' 
					sys.exit()

				# It looks like they want to send a message to someone.
				elif (split_message[0].lower() == 'sendto'):
					for index, word in enumerate(split_message):
						if index == 1:
							# Parse out the target of the message.
							target_client = word
						elif index == 2:
							# Did they include the 'message' part of the command?
							message_literal = word.lower()
							if (message_literal != 'message'):
								print 'sendto <client\'s name> message <your message>'
					# The rest must be the text of their message.
					message_text = split_message[3:] 

					print 'target_client ', target_client
					print 'message_literal ', message_literal
					print 'message_text ', message_text

					client_socket.send(message)
				
				else:
					print 'That was not a valid command.'
					#except:
					#	print 'exception'
					#	print 'sendto <client\'s name> message <your message>'

				# At the very end...
				# Display the input prompt.
				sys.stdout.write('[' + client_name + ']: ')
				sys.stdout.flush() 
if __name__ == "__main__":

	sys.exit(client())