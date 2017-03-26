#!/usr/bin/env python

'''
pinger.py
Alan Coon
alancoon@usc.edu
'''

import os
import sys
import socket
import time
import struct
import select

def pinger ():
	# Make a dictionary to keep track of which flags have been used in the 
	# command line call.
	flag_used = {}
	flag_used['d'] = False
	flag_used['p'] = False
	flag_used['l'] = False
	flag_used['c'] = False

	# Instantiate the variables.
	logfile 	= None
	payload 	= None
	count  		= None
	destination = None

	# Parse through the command line call.
	for index, word in enumerate(sys.argv):

		# If the current word we are inspecting begins with an en-dash,
		# then read the flag and see if it matches any of our known flags.
		if (word[0] == '-'):
			flag = word[1].lower()
			try:
				# Incase the user doesn't use the proper formatting, we will
				# raise an exception.  Not the best way to do this but
				# I'm not getting paid for this.
				next_arg = sys.argv[index + 1]
				if next_arg[0] == '-':
					raise
			except:
				print_instructions()
				sys.exit()

			# Each flag can be substituted in for their fullname.
			if (flag == 'd' or flag == '-dst'):
				destination = next_arg
				flag_used['d'] = True

			elif (flag == 'p' or flag == '-payload'):
				payload = next_arg
				flag_used['p'] = True

			elif (flag == 'l' or flag == '-logfile'):
				logfile = next_arg
				flag_used['l'] = True

			elif (flag == 'c' or flag == '-count'):
				count = next_arg
				flag_used['c'] = True

			# If the flag doesn't exist, print instructions and cleanly terminate.
			else:
				print_instructions()
				sys.exit()

	# Check to see if the user entered a valid combination of flags.
	check_validity(flag_used, destination, payload, logfile, count)

	for i in range(count):
		icmp = socket.getprotobyname('icmp')
		try:
			connection = socket.socket(socket.AF_INET, socket.SOCK_RAW, icmp)
		except socket.error, (errno, msg):
			if (errno == 1):
				msg = msg + ' – Please run again with root privilege.'
				raise socket.error(msg)
			else:
				raise
		my_id = os.getpid() & 0xFFFF
		# Hardcode the ping size to 64.
		send_ping(connection, destination, my_id, 64) 
		# Receive with hardcoded timeout of 2.
		delay = receive_response(connection, my_id, 2)

		connection.close()
		print 'delay: ' + str(delay)


	# Attempt to create the socket using SOCK_RAW.
	try:
		connection = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW)
		connection.bind((destination, 0))
	except socket.error, msg:
		print 'Socket could not be created. Error code: ' + str(msg[0]) + ' Message: ' + msg[1]
		sys.exit()

	print 'Pinging ' + destination + ' with ' + str(len(payload)) + ' bytes of data \"' + payload + '\"'

	source = socket.gethostbyname(socket.gethostname())
	timeout = 1

	for num in range(int(count)):
		payload = struct.pack('!HH', 1234, num) + payload
		connection.connect((destination, 80))
		connection.sendall(b'\x08\0' + checksum(b'\x08\0\0\0' + payload) + payload)
		start = time.time()

		while select.select([connection], [], [], max(0, start + timeout - time.time()))[0]:
				data = connection.recv(65536)
				if len(data) < 20 or len(data) < struct.unpack_from('!xxH', data)[0]:
					continue
				if data[20:] == b'\0\0' + checksum(b'\0\0\0\0' + payload) + payload:
					print time.time() - start
					break


def check_validity (flags, d, p, l, c):
	print flags
	if flags['c'] and flags['p'] and flags['d']:
		print 'Validity check passed'
	else:
		print 'Validity check failed'
		if (flags['l']):
			print 'logfile: ' + l
		if (flags['p']):
			print 'payload: ' + p
		if (flags['c']):
			print 'count: ' + c
		if (flags['d']):
			print 'destination: ' + d
		print_instructions()
		sys.exit()

def checksum(data):
    x = sum(x << 8 if i % 2 else int(x) for i, x in enumerate(data)) & 0xFFFFFFFF
    x = (x >> 16) + (x & 0xFFFF)
    x = (x >> 16) + (x & 0xFFFF)
    return struct.pack('<H', ~x & 0xFFFF)

def print_instructions ():
	print 'pinger [-l file] -p \"data\" -c N -d IP'
	print '\t-l, --logfile  Write the debug info to the specified log file'
	print '\t-p, --payload  The string to include in the payload'
	print '\t-c, --count    The number of packets used to compute RTT'
	print '\t-d, --dst      The destination IP for the ping message'

def main ():
	pinger()

if __name__ == "__main__":
	main()