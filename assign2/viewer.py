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
import pcapy
from datetime import datetime

pcap = None
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

	pcapy.findalldevs()
	max_bytes = 1024
	promiscuous = False
	read_timeout = 100 # in milliseconds
	cap = pcapy.open_live(interface, max_bytes, promiscuous, read_timeout)
	print 'viewer: listening on ' + interface
	if file:
		file.write('viewer: listening on ' + interface + '\n')
	#start sniffing packets
	if (flag_used['c']):
		packets_sniffed = 0
		while packets_sniffed < count:
			(header, packet) = cap.next()
			if header:
				to_print = parse_packet(packet)
				if to_print:
					print to_print
					if file:
						file.write(to_print + '\n')
				packets_sniffed = packets_sniffed + 1
	else:	
		while True:
			(header, packet) = cap.next()
			if header:
				to_print = parse_packet(packet)
				if to_print:
					print to_print	
					if file:
						file.write(to_print + '\n')

def eth_addr (a) :
    b = "%.2x:%.2x:%.2x:%.2x:%.2x:%.2x" % (ord(a[0]) , ord(a[1]) , ord(a[2]), ord(a[3]), ord(a[4]) , ord(a[5]))
    return b

def parse_packet (packet):
	# Parse ethernet header.
	eth_length = 14
	eth_header = packet[:eth_length]
	eth = struct.unpack('!6s6sH' , eth_header)
	eth_protocol = socket.ntohs(eth[2])
	#print 'Destination MAC : ' + eth_addr(packet[0:6]) + ' Source MAC : ' + eth_addr(packet[6:12]) + ' Protocol : ' + str(eth_protocol)

	#Parse IP packets, IP Protocol number = 8
	if eth_protocol == 8 :
		#Parse IP header
		#take first 20 characters for the ip header
		ip_header = packet[eth_length:20+eth_length]
		 
		iph = struct.unpack('!BBHHHBBH4s4s' , ip_header)
 
		version_ihl = iph[0]
		version = version_ihl >> 4
		ihl = version_ihl & 0xF
 
		iph_length = ihl * 4
 
		ttl = iph[5]
		protocol = iph[6]
		s_addr = socket.inet_ntoa(iph[8]);
		d_addr = socket.inet_ntoa(iph[9]);
 
		#print 'Version : ' + str(version) + ' IP Header Length : ' + str(ihl) + ' TTL : ' + str(ttl) + ' Protocol : ' + str(protocol) + ' Source Address : ' + str(s_addr) + ' Destination Address : ' + str(d_addr)
 	
	 	if protocol:
			u = iph_length + eth_length
			icmph_length = 4 + 4
			icmp_header = packet[u:u + icmph_length]

			icmph = struct.unpack('!BBHHH' , icmp_header)
			 
			icmp_type = icmph[0]
			code = icmph[1]
			checksum = icmph[2]
			identifier = icmph[3]
			seq_number = icmph[4]

			#print 'icmp_type' + str(icmp_type)
			#print 'code ' + str(code)

			echo_type = ''
			
			h_size = eth_length + iph_length + icmph_length
			data_size = len(packet) - h_size
			 
			data = packet[h_size:]

			if code == 0:
				if icmp_type == 0:
					echo_type = 'reply'
					time_stamp = str(time.time()).split('.')[0] + '.' + str(datetime.now()).split('.')[1]
					to_print = str(time_stamp) + ' ' + str(s_addr) + ' > ' + str(d_addr) + ': ICMP echo ' + echo_type + ', id ' + str(identifier) + ', length ' + str(data_size)
					return to_print
				elif icmp_type == 8:
					echo_type = 'request'
					time_stamp = str(time.time()).split('.')[0] + '.' + str(datetime.now()).split('.')[1]
					to_print = str(time_stamp) + ' ' + str(s_addr) + ' > ' + str(d_addr) + ': ICMP echo ' + echo_type + ', id ' + str(identifier) + ', length ' + str(data_size)
					return to_print
			else:
				return ''


def check_validity (flags, i, r, c, l):
	global pcap, file
	if flags['i']:
		if flags['c']:
			if c < 0:
				print 'Count must be at least 0.'
				return False
		if flags['r']:
			try:
				pcap = open(r, 'r')
			except:
				print 'Invalid pcap file.'
				return False
		if flags['l']:
			try:
				file = open(l, 'w')
			except:
				print 'Invalid logfile.'
				return False
		return True
	else:
		print 'Interface flag required.'
		return False

def print_instructions ():
	print 'viewer -i interface [-r filename] [-c N] [-l logfile]'
	print '\t-i, --int  	Listen on the specified interface'
	print '\t-r, --read  	Read the pcap file and print packets'
	print '\t-c, --count    Print N number of packets and quit'
	print '\t-l, --logfile  Write debug info to the specified log'

def main ():
	viewer()

if __name__ == "__main__":
	main()