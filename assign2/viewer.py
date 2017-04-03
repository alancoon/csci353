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
import dpkt
# I'm not sure how importing works because I'm getting inconsistent resutls.
from dpkt.compat import compat_ord
from dpkt import pcap
from dpkt import ip
from dpkt import ethernet
from datetime import datetime

pcap_obj = None
pcap_file = None
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
	if flag_used['i']:
		pcapy.findalldevs()
		cap = pcapy.open_live(interface, 1024, False, 100) # 100 millisecond timeout
		print 'viewer: listening on ' + interface
		if file:
			file.write('viewer: listening on ' + interface + '\n')
		# Start sniffing packets, if c flag is specified then only sniff N packets.
		packets_sniffed = 0
		if (flag_used['c']):
			while int(packets_sniffed) < int(count):
				(header, packet) = cap.next()
				if header:
					to_print = parse_packet(packet)
					if to_print:
						print to_print
						if file:
							file.write(to_print + '\n')
						packets_sniffed = packets_sniffed + 1

		# Otherwise we sniff packets forever.
		else:	
			while True:
				(header, packet) = cap.next()
				if header:
					to_print = parse_packet(packet)
					if to_print:
						print to_print	
						if file:
							file.write(to_print + '\n')
	elif flag_used['r']:
		# For each packet in the pcap process the contents
		pcap = pcap_obj
		packets_sniffed = 0
		for timestamp, buf in pcap:
			# Procedure for using the dpkt library to parse pcap files is borrowed from
			# dpkt documentation, as well as several supplementary subroutines. 
			# Get the microseconds from the UTC time, and the time since epoch using
			# the plain timestamp.  Concatenate them together.
			microseconds = str(datetime.utcfromtimestamp(timestamp)).split('.')[1]
			seconds = str(timestamp).split('.')[0]
			time = seconds + '.' + microseconds

			# Start concatenating the string that we're going to print.
			to_print = time

			# Unpack the Ethernet frame.
			eth = dpkt.ethernet.Ethernet(buf)

			# Make sure the Ethernet frame contains an IP packet.
			# If it doesn't, print an explanation and skip over this iteration.
			if not isinstance(eth.data, dpkt.ip.IP):
				print 'Non IP Packet type not supported %s' % eth.data.__class__.__name__
				if file:
					file.write('Non IP Packet type not supported ' + eth.data.__class__.__name__ + '\n')
				continue

			# Now unpack the data within the Ethernet frame (the IP packet).
			# Pulling out src, dst, length, fragment info, TTL, and Protocol.
			ip = eth.data

			if isinstance(ip.data, dpkt.icmp.ICMP):
				icmp = ip.data

				# Pull out fragment information (flags and offset all packed into off field, so use bitmasks)
				do_not_fragment = bool(ip.off & dpkt.ip.IP_DF)
				more_fragments = bool(ip.off & dpkt.ip.IP_MF)
				fragment_offset = ip.off & dpkt.ip.IP_OFFMASK

				# Add the IP addresses to the string.
				to_print = to_print + ' ' + inet_to_str(ip.src) + ' > ' + inet_to_str(ip.dst) + ': '
				
				# Add whether it's an echo request or reply.
				if (icmp.type == 0 and icmp.code == 0):
					to_print = to_print + 'ICMP echo reply, '
				elif (icmp.type == 8 and icmp.code == 0):
					to_print = to_print + 'ICMP echo request, '

				# The ID number is embedded within the data so we need to parse a little to get it.
				icmp_data = repr(icmp.data)
				icmp_id = icmp_data.split(',')[0][8:]

				# Finalize the print string.
				to_print = to_print + 'id ' + icmp_id + ', length ' + str(ip.len)

				# Finish it off.
				print to_print
				if file:
					file.write(to_print + '\n')

				# Increment the number of packets sniffed if the -c flag was used.
				if flag_used['c']:
					packets_sniffed = packets_sniffed + 1
					if not packets_sniffed < int(count):
						if file:
							file.close()
						if pcap_file:
							pcap_file.close()
						sys.exit()

def mac_addr(address):
	''' Borrowed. '''
	return ':'.join('%02x' % compat_ord(b) for b in address)

def inet_to_str(inet):
	''' Borrowed. '''
	try:
		return socket.inet_ntop(socket.AF_INET, inet)
	except ValueError:
		return socket.inet_ntop(socket.AF_INET6, inet)

def parse_packet (packet):
	# Parse ethernet header.
	eth_header = packet[:14]
	eth = struct.unpack('!6s6sH' , eth_header)
	eth_protocol = socket.ntohs(eth[2])

	# The IP we are looking for is 8.
	if eth_protocol == 8 :
		# Unpack the IP header for information.
		ip_header = packet[14:34]
		ip_header = struct.unpack('!BBHHHBBH4s4s' , ip_header)
		version_ihl = ip_header[0]
		version = version_ihl >> 4
		ihl = version_ihl & 0xF
		ip_header_length = ihl * 4
		protocol = ip_header[6]
		source_address = socket.inet_ntoa(ip_header[8]);
		destination_address = socket.inet_ntoa(ip_header[9]);
	
		# If the protcol is 1 (ICMP):
		if protocol:
			# Unpack the ICMP header for information we need.
			ip_eth_length = ip_header_length + 14
			icmp_header = packet[ip_eth_length:ip_eth_length + 8]
			icmp_header = struct.unpack('!BBHHH', icmp_header)
			icmp_type = icmp_header[0]
			code = icmp_header[1]
			identifier = icmp_header[3]
			header_length = 14 + ip_header_length + 8
			data_size = len(packet) - header_length
			data = packet[header_length:]

			# Both have code of 0 but reply has a type of 0 and request has a type of 8.
			if code == 0:
				if icmp_type == 0:
					echo_type = 'reply'
					time_stamp = str(time.time()).split('.')[0] + '.' + str(datetime.now()).split('.')[1]
					to_print = str(time_stamp) + ' ' + str(source_address) + ' > ' + str(destination_address) + ': ICMP echo ' + echo_type + ', id ' + str(identifier) + ', length ' + str(data_size)
					return to_print
				elif icmp_type == 8:
					echo_type = 'request'
					time_stamp = str(time.time()).split('.')[0] + '.' + str(datetime.now()).split('.')[1]
					to_print = str(time_stamp) + ' ' + str(source_address) + ' > ' + str(destination_address) + ': ICMP echo ' + echo_type + ', id ' + str(identifier) + ', length ' + str(data_size)
					return to_print
			else:
				return ''


def check_validity (flags, i, r, c, l):
	global pcap_obj, file, pcap_file
	if flags['i']:
		if flags['c']:
			if c < 0:
				print 'Count must be at least 0.'
				return False
		if flags['r']:
			print 'Read and interface flags must be used exclusively.'
			return False
		if flags['l']:
			try:
				file = open(l, 'w')
			except:
				print 'Invalid logfile.'
				return False
		return True
	elif flags['r']:
		try:
			if flags['l']:
				try:
					file = open(l, 'w')
				except:
					print 'Invalid logfile.'
					return False
			pcap_file = open(r, 'r')
			pcap_obj = pcap.Reader(pcap_file)
			return True
		except:
			print 'Invalid pcap file.'
			raise
			return False
	else:
		print 'Interface or read flag required.'
		return False

def print_instructions ():
	print './viewer.py -i interface [-r filename] [-c N] [-l logfile]'
	print '\t-i, --int  	Listen on the specified interface'
	print '\t-r, --read  	Read the pcap file and print packets'
	print '\t-c, --count    Print N number of packets and quit'
	print '\t-l, --logfile  Write debug info to the specified log'
	print 'Only use each flag once at most.'

def main ():
	try:
		viewer()
	except KeyboardInterrupt:
		if file:
			file.close()
		if pcap_file:
			pcap_file.close()

if __name__ == "__main__":
	main()