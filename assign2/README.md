# README.md


Alan Coon


alancoon@usc.edu


7561574891


# Language and Version


I am using Python 2.7.10 for this assignment.


# Dependencies


Professor Hussain granted me permission to use the dpkt library for this assignment.  I use it for my implementation of the viewer.  Because of the way that the library is implemented, I borrowed some of their simple subroutines for simple tasks, such as converting an IP address into a string.  


I included a very simple bash script to install dpkt on your computer.  To use it enter "bash install_dpkt.sh" on your terminal.  Alternatively enter the command "sudo pip install dpkt".


I also use pcapy for the pinger.


# Pinger


To run the pinger, enter the following into your terminal:


    sudo ./pinger.py -d IP -c N -p "data" [-l file]


        -d, --dst      The destination IP for the ping message


        -c, --count    The number of packets used to compute RTT


        -p, --payload  The string to include in the payload


        -l, --logfile  (Optional) Write the debug info to the specified log file


Only use each flag once at most.  Use sudo because root access is required to make your own packets.


# Viewer


To run the viewer, enter the following into your terminal:


    ./viewer.py [-i interface] [-r filename] [-c N] [-l logfile]


        -i, --int       (*) Listen on the specified interface


        -r, --read  	(*) Read the pcap file and print packets


        -c, --count     (Optional) Print N number of packets and quit


        -l, --logfile   (Optional) Write debug info to the specified log


Only use each flag once at most. If no count flag is specified for the viewer, it will execute indefinitely or until the end of the pcap file.


(*) The interface and read flags MUST be used exclusively, the viewer cannot do both at the same time.  Please re-run the command instead of combining both flags into one execution.


# Direct Execution 


To allow direct execution, I used "sudo chmod +x pinger.py" and "sudo chmod +x viewer.py" and added directives at the top of both scripts to execute using whatever version of Python is default on the computer.
