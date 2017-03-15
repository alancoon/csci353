#!/usr/bin/env python

'''
pinger.py
Alan Coon
alancoon@usc.edu
'''

import sys
import socket

def pinger ():

	flag_used = {}
	flag_used['d'] = False
	flag_used['p'] = False
	flag_used['l'] = False
	flag_used['c'] = False

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


			if (flag == 'd' or flag == '-dst'):
				destination = next_word
				flag_used['d'] = True

			elif (flag == 'p' or flag == '-payload'):
				# Combine the argv into one string then split by double-quotes.
				print sys.argv
				print ' '.join(sys.argv)
				argv_split = (' '.join(sys.argv)).split('\"')
				if (len(argv_split) != 3):
					# If the size of the array isn't 3, which means we have two double-quotes,
					# then we know something is wrong because the user is putting more
					# double-quotes than he or she should.
					payload = argv_split[1]
				else:
					print_instructions()
					sys.exit()

			elif (flag == 'l' or flag == '-logfile'):
				logfile = next_word
				flag_used['l'] = True

			elif (flag == 'c' or flag == '-count'):
				count = next_word
				flag_used['c'] = True

			else:
				print_instructions()
				sys.exit()

	check_validity(flag_used)

	if (flag_used['l']):
		print 'logfile: ' + logfile
	print 'payload: ' + payload
	print 'count: ' + count
	print 'destination: ' + destination

	try:
		s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW)
		s.bind((destination, 0))
	except socket.error, msg:
		print 'Socket could not be created. Error code: ' + str(msg[0]) + ' Message: ' + msg[1]
		sys.exit()


	source = socket.gethostbyname(socket.gethostname())

	# ip header fields
	ip_ihl = 5
	ip_ver = 4
	ip_tos = 0
	ip_tot_len = 0  # kernel will fill the correct total length
	ip_id = 54321   #Id of this packet
	ip_frag_off = 0
	ip_ttl = 255
	ip_proto = socket.IPPROTO_TCP
	ip_check = 0    # kernel will fill the correct checksum
	ip_saddr = socket.inet_aton(source)   #Spoof the source ip address if you want to
	ip_daddr = socket.inet_aton(destination)

	ip_ihl_ver = (ip_ver << 4) + ip_ihl
	tcp_header = pack('!HHLLBBHHH' , tcp_source, tcp_dest, tcp_seq, tcp_ack_seq, tcp_offset_res, tcp_flags,  tcp_window, tcp_check, tcp_urg_ptr)

	# Header fields
	source_address = socket.inet_aton(source)
	destination_address = socket.inet_aton(destination)
	placeholder = 0
	protocol = socket.IPPROTO_TCP
	tcp_length = len(tcp_header) + len(user_data)
	 
	psh = pack('!4s4sBBH' , source_address , destination_address , placeholder , protocol , tcp_length);
	psh = psh + tcp_header + user_data;
	 
	tcp_check = 1 # checksum(psh)
	 
	# make the tcp header again and fill the correct checksum - remember checksum is NOT in network byte order
	tcp_header = pack('!HHLLBBH' , tcp_source, tcp_dest, tcp_seq, tcp_ack_seq, tcp_offset_res, tcp_flags,  tcp_window) + pack('H' , tcp_check) + pack('!H' , tcp_urg_ptr)
	 
	# final full packet - syn packets dont have any data
	packet = ip_header + tcp_header + user_data
	 
	#Send the packet finally - the port specified has no effect
	s.sendto(packet, (destination , 0 ))    # put this in a loop if you want to flood the target

def check_validity (flags):
	if not flags['c'] or not flags['p'] or not flags['d']:
		print_instructions()
		sys.exit()


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