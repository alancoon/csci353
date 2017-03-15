#!/usr/bin/env python

'''
pinger.py
Alan Coon
alancoon@usc.edu
'''

import sys
import socket
from struct import *

def pinger ():

	flag_used = {}
	flag_used['d'] = False
	flag_used['p'] = False
	flag_used['l'] = False
	flag_used['c'] = False

	logfile 	= None
	payload 	= None
	count  		= None
	destination = None

	for index, word in enumerate(sys.argv):

		if (word[0] == '-'):
			flag = word[1].lower()
			try:
				next_arg = sys.argv[index + 1]
				if next_arg[0] == '-':
					raise
			except:
				print_instructions()
				sys.exit()

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

			else:
				print_instructions()
				sys.exit()


	check_validity(flag_used, destination, payload, logfile, count)




	try:
		s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW)
		s.bind((destination, 0))
	except socket.error, msg:
		print 'Socket could not be created. Error code: ' + str(msg[0]) + ' Message: ' + msg[1]
		sys.exit()

	print 'Pinging ' + destination + ' with ' + len(payload) + ' bytes of data \"' + payload + '\"'

	source = socket.gethostbyname(socket.gethostname())

	# ip header fields
	ip_ihl = 5
	ip_ver = 4
	ip_tos = 0
	ip_tot_len = 0  # kernel will fill the correct total length
	ip_id = 0   #Id of this packet
	ip_frag_off = 0
	ip_ttl = 255
	ip_proto = socket.IPPROTO_TCP
	ip_check = 0    # kernel will fill the correct checksum
	ip_saddr = socket.inet_aton(source)   #Spoof the source ip address if you want to
	ip_daddr = socket.inet_aton(destination)

	ip_ihl_ver = (ip_ver << 4) + ip_ihl

	# the ! in the pack format string means network order
	ip_header = pack('!BBHHHBBH4s4s' , ip_ihl_ver, ip_tos, ip_tot_len, ip_id, ip_frag_off, ip_ttl, ip_proto, ip_check, ip_saddr, ip_daddr)


	# tcp header fields
	tcp_source = 1234   # source port
	tcp_dest = 80   # destination port
	tcp_seq = 454
	tcp_ack_seq = 0
	tcp_doff = 5    #4 bit field, size of tcp header, 5 * 4 = 20 bytes
	#tcp flags
	tcp_fin = 0
	tcp_syn = 1
	tcp_rst = 0
	tcp_psh = 0
	tcp_ack = 0
	tcp_urg = 0
	tcp_window = socket.htons (5840)    #   maximum allowed window size
	tcp_check = 0
	tcp_urg_ptr = 0
	 
	tcp_offset_res = (tcp_doff << 4) + 0
	tcp_flags = tcp_fin + (tcp_syn << 1) + (tcp_rst << 2) + (tcp_psh <<3) + (tcp_ack << 4) + (tcp_urg << 5)


	tcp_header = pack('!HHLLBBHHH' , tcp_source, tcp_dest, tcp_seq, tcp_ack_seq, tcp_offset_res, tcp_flags,  tcp_window, tcp_check, tcp_urg_ptr)

	# Header fields
	source_address = socket.inet_aton(source)
	destination_address = socket.inet_aton(destination)
	placeholder = 0
	protocol = socket.IPPROTO_TCP
	tcp_length = len(tcp_header) + len(payload)
	 
	psh = pack('!4s4sBBH' , source_address , destination_address , placeholder , protocol , tcp_length);
	psh = psh + tcp_header + payload;
	 
	tcp_check = 1 # checksum(psh)
	 
	# make the tcp header again and fill the correct checksum - remember checksum is NOT in network byte order
	tcp_header = pack('!HHLLBBH' , tcp_source, tcp_dest, tcp_seq, tcp_ack_seq, tcp_offset_res, tcp_flags,  tcp_window) + pack('H' , tcp_check) + pack('!H' , tcp_urg_ptr)
	 
	# final full packet - syn packets dont have any data
	packet = ip_header + tcp_header + payload
	 
	#Send the packet finally - the port specified has no effect
	s.sendto(packet, (destination , 0 ))    # put this in a loop if you want to flood the target

def check_validity (flags, d, p, l, c):
	print flags
	if flags['c'] and flags['p'] and flags['d']:
		print 'Validity check passed'
	else:
		print 'Validity check failed'
		if (flags['l']):
			print 'logfile: ' + l
		print 'payload: ' + p
		print 'count: ' + c
		print 'destination: ' + d
		print_instructions()
		sys.exit()

def checksum(data):
    x = sum(x << 8 if i % 2 else x for i, x in enumerate(data)) & 0xFFFFFFFF
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
	#try:
	pinger()
	'''
	except KeyboardInterrupt:
		print 'exit'
		clean_up()
	finally:
		clean_up()
	'''


if __name__ == "__main__":
	main()