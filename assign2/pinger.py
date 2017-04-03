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

file = None

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
	valid = validify_input(flag_used, destination, payload, logfile, count)
	if not valid:
		print_instructions()
		sys.exit()

	# Print out the pinging statement to the user's terminal.
	print 'Pinging ' + destination + ' with ' + str(len(payload)) + ' bytes of data \"' + payload + '\":'
	if file:
		file.write('Pinging ' + destination + ' with ' + str(len(payload)) + ' bytes of data \"' + payload + '\":\n')
	# We will collect delay statistics in the statistics array.
	statistics = []

	# We want to send count number of pings.
	for i in range(int(count)):
		icmp = socket.getprotobyname('icmp')
		try:
			connection = socket.socket(socket.AF_INET, socket.SOCK_RAW, icmp)
		except socket.error, (errno, msg):
			if (errno == 1):
				msg = msg + ' - Please run again with root privilege.'
				raise socket.error(msg)
			else:
				raise
		my_id = os.getpid() & 0xFFFF
		
		# Send out the ping.
		send_ping(connection, destination, my_id, payload) 

		# Receive with hardcoded timeout of 2.
		(delay, data, TTL) = receive_response(connection, my_id, 2)
		
		if delay == -1:
			# No response, we timed out.
			print '  Request timeout for ' + destination + ' attempt ' + str(i)
			if file:
				file.write('  Request timeout for ' + destination + ' attempt ' + str(i) + '\n')
		else: 
			# We received a response.
			milliseconds = int(delay * 1000)
			no_bytes = len(data)
			connection.close()
			print '  Reply from ' + destination + ': bytes=' + str(no_bytes) + ' time=' + str(milliseconds) + 'ms TTL=' + str(TTL)
			if file:
				file.write('  Reply from ' + destination + ': bytes=' + str(no_bytes) + ' time=' + str(milliseconds) + 'ms TTL=' + str(TTL) + '\n')
			statistics.append(milliseconds)
	
	# Now that we are all done, print the statistics to the user's terminal.
	if statistics:
		print_statistics(destination, count, statistics)
	if file:
		file.close()

def print_statistics (destination, count, statistics):
	packets_lost = int(count) - len(statistics)
	loss_rate = int(float(packets_lost) / float(count) * float(100))
	minimum = min(statistics)
	maximum = max(statistics)
	average = sum(statistics) / len(statistics)
	print 'Ping statistics for ' + destination + ':'
	print '  Packets: Sent = ' + str(count) + ', Received = ' + str(len(statistics)) + ', Lost = ' + str(packets_lost) + ' (' + str(loss_rate) + '% loss),'
	print '  Approximate round trip times in milli-seconds:'
	print '  Minimum = ' + str(minimum) + 'ms, Maximum = ' + str(maximum) + 'ms, Average = ' + str(average) + 'ms'
	if file:
		file.write('Ping statistics for ' + destination + ':\n')
		file.write('  Packets: Sent = ' + str(count) + ', Received = ' + str(len(statistics)) + ', Lost = ' + str(packets_lost) + ' (' + str(loss_rate) + '% loss),\n')
		file.write('  Approximate round trip times in milli-seconds:\n')
		file.write('  Minimum = ' + str(minimum) + 'ms, Maximum = ' + str(maximum) + 'ms, Average = ' + str(average) + 'ms\n')

def validify_input (flags, d, p, l, c):
	global file
	if flags['c'] and flags['p'] and flags['d']:
		if c < 0:
			print 'Count must be at least 0.'
			return False
		if flags['l']:
			try:
				file = open(l, 'w')
			except:
				print 'Invalid logfile.'
				return False
		return True
	else:
		print 'Count, payload, and destination required.'
		return False

def send_ping (connection, destination, my_id, payload):
	try:
		destination = socket.gethostbyname(destination)
	except:
		print 'Invalid IP or address.'
		sys.exit()

	# Set up the packet.
	packet_size = len(payload) - 8
	my_checksum = 0

	# Pack it up.
	# ICMP_ECHO_REQUEST is 8.
	header = struct.pack('bbHHh', 8, 0, my_checksum, my_id, 1)
	data = struct.pack('d', time.time()) + payload
	my_checksum = checksum(header + data)
	header = struct.pack('bbHHh', 8, 0, socket.htons(my_checksum), my_id, 1)
	packet = header + data

	# Send out the packet.
	connection.sendto(packet, (destination, 1)) 

def receive_response (connection, id_no, timeout):
	time_left = timeout
	while True:
		started_select = time.time()
		ready = select.select([connection], [], [], time_left)
		wait_time = (time.time() - started_select)

		# If the ready list is empty then we timeout.
		if ready[0] == []: 
			return (-1, None, -1)

		# Begin the "stopwatch" as we receive the packet.
		time_received = time.time()
		received_packet, address = connection.recvfrom(1024)
		
		# Get TTL.
		ip_header = received_packet[33:34]
		ip_header = struct.unpack('B', ip_header)
		TTL = ip_header[0]

		# Get data from the ICMP header.
		icmp_header = received_packet[20:28]
		data = received_packet[36:]
		icmp_type, code, checksum, identifier, sequence = struct.unpack('bbHHh', icmp_header)

		if identifier == id_no:
			packet_bytes = struct.calcsize('d')
			time_sent = struct.unpack('d', received_packet[28:28 + packet_bytes])[0]
			return (time_received - time_sent, data, TTL)

		time_left = time_left - wait_time

		# Another timeout check.
		if time_left <= 0:
			return (-1, None, -1)

def checksum(data):
	sum = 0
	count_to = (len(data) / 2) * 2
	for count in xrange(0, count_to, 2):
		this = ord(data[count + 1]) * 256 + ord(data[count])
		sum = sum + this

	if count_to < len(data):
		sum = sum + ord(data[len(data) - 1])

	sum = (sum >> 16) + (sum & 0xffff)
	sum = sum + (sum >> 16)
	answer = ~sum
	answer = answer & 0xffff
	answer = answer >> 8 | (answer << 8 & 0xff00)
	return answer

def print_instructions ():
	print './pinger.py -d IP -c N -p \"data\" [-l file]'
	print '\t-d, --dst      The destination IP for the ping message'
	print '\t-c, --count    The number of packets used to compute RTT'
	print '\t-p, --payload  The string to include in the payload'
	print '\t-l, --logfile  Write the debug info to the specified log file'
	print 'Only use each flag once at most.'

def main ():
	pinger()

if __name__ == "__main__":
	main()