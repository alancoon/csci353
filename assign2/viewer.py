#!/usr/bin/env python

'''
pinger.py
Alan Coon
alancoon@usc.edu
'''

import sys
import socket
import time
import struct

file = None

def viewer ():
	# Make a dictionary to keep track of which flags have been used in the 
	# command line call.
	flag_used = {}
	flag_used['i'] = False
	flag_used['r'] = False
	flag_used['c'] = False
	flag_used['l'] = False

	# Instantiate the variables.
	interface 	= None
	read	 	= None
	count  		= None
	logfile		= None

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
			if (flag == 'i' or flag == '-int'):
				interface = next_arg
				flag_used['i'] = True

			elif (flag == 'r' or flag == '-read'):
				read = next_arg
				flag_used['r'] = True

			elif (flag == 'c' or flag == '-count'):
				count = next_arg
				flag_used['c'] = True

			elif (flag == 'l' or flag == '-logfile'):
				logfile = next_arg
				flag_used['l'] = True

			# If the flag doesn't exist, print instructions and cleanly terminate.
			else:
				print_instructions()
				sys.exit()

	# Check to see if the user entered a valid combination of flags.
	valid = check_validity(flag_used, interface, read, count, logfile)
	if not valid:
		print_instructions()
		sys.exit()



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


def check_validity (flags, i, r, c, l):
	if flags['i']:
		if flags['l']:
			try:
				file = open(l, 'w')
				return True
			except:
				print 'Invalid logfile.'
				return False
		else:
			return True
	else:
		print 'Validity check failed'

		if (flags['i']):
			print 'int: ' + i
		if (flags['r']):
			print 'read: ' + r
		if (flags['c']):
			print 'count: ' + c
		if (flags['l']):
			print 'logfile: ' + l
		return False


def print_instructions ():
	print 'viewer [-l logfile] -i interface -c N –r filename'
	print '\t-i, --int  	Listen on the specified interface'
	print '\t-r, --read  	Read the pcap file and print packets'
	print '\t-c, --count    Print N number of packets and quit'
	print '\t-l, --logfile  Write debug info to the specified log'

def main ():
	viewer()

if __name__ == "__main__":
	main()