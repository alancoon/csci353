from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.topology.event import EventSwitchEnter, EventSwitchLeave
from ryu.lib.mac import haddr_to_bin
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types

from topology import load_topology
import networkx as nx

# This function takes as input a networkx graph. It then computes
# the minimum Spanning Tree, and returns it, as a networkx graph.
def compute_spanning_tree(G):

    # The Spanning Tree of G
    ST = nx.minimum_spanning_tree(G)
    return ST

class L2Forwarding(app_manager.RyuApp):
    def __init__(self, *args, **kwargs):
        super(L2Forwarding, self).__init__(*args, **kwargs)

        # Load the topology
        topo_file = 'topology.txt'
        self.G = load_topology(topo_file)

        # For each node in the graph, add an attribute mac-to-port
        for n in self.G.nodes():
            self.G.add_node(n, mactoport={})

        # Compute a Spanning Tree for the graph G
        self.ST = compute_spanning_tree(self.G)

        print self.get_str_topo(self.G)
        print self.get_str_topo(self.ST)

    # This method returns a string that describes a graph (nodes and edges, with
    # their attributes). You do not need to modify this method.
    def get_str_topo(self, graph):
        res = 'Nodes\tneighbors:port_id\n'

        att = nx.get_node_attributes(graph, 'ports')
        for n in graph.nodes_iter():
            res += str(n)+'\t'+str(att[n])+'\n'

        res += 'Edges:\tfrom->to\n'
        for f in graph:
            totmp = []
            for t in graph[f]:
                totmp.append(t)
            res += str(f)+' -> '+str(totmp)+'\n'

        return res

    # This method returns a string that describes the Mac-to-Port table of a
    # switch in the graph. You do not need to modify this method.
    def get_str_mactoport(self, graph, dpid):
        res = 'MAC-To-Port table of the switch '+str(dpid)+'\n'

        for mac_addr, outport in graph.node[dpid]['mactoport'].items():
            res += str(mac_addr)+' -> '+str(outport)+'\n'

        return res.rstrip('\n')

    # This method associates a MAC address with a port on a node given by the datapath ID.
    def add_mactoport_entry(self, dpid, mac, port):
        self.G.node[dpid][mac] = port


    def mactoport_entry_exists(self, dpid, mac):
        return mac in self.G.node[dpid]


    def get_mactoport_port(self, dpid, mac):
        return self.G.node[dpid][mac]

    @set_ev_cls(EventSwitchEnter)
    def _ev_switch_enter_handler(self, ev):
        print('enter: %s' % ev)

    @set_ev_cls(EventSwitchLeave)
    def _ev_switch_leave_handler(self, ev):
        print('leave: %s' % ev)

    # This method is called every time an OF_PacketIn message is received by 
    # the switch. Here we must calculate the best action to take and install
    # a new entry on the switch's forwarding table if necessary
    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        ofproto_parser = datapath.ofproto_parser

    # Getting the IP addresses of the source and destination through the ethernet header.
        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)

    # Ignore LLDP packet types.
        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            return

    # Grab the MAC addresses of the source and destination.
        dst = eth.dst
        src = eth.src

    # This is the ID of the current node we are on.
        dpid = datapath.id


        print ('\n\nI am node', dpid)
        print ('My dst is', dst, 'and my src is', src)
        print (datapath)

    # Associate the source MAC address with the port number we received the message from.
        self.add_mactoport_entry(dpid, src, msg.in_port)

    # Check if the destination is in the node's MAC address dictionary.
        if self.mactoport_entry_exists(dpid, dst):
            out_port = self.get_mactoport_port(dpid, dst)
            print('Entry exists', str(out_port), 'from', dpid)

        else:
            out_port = ofproto.OFPP_FLOOD
            print('No entry on', dpid)

        actions = [ofproto_parser.OFPActionOutput(out_port)]

        out = ofproto_parser.OFPPacketOut(
            datapath=datapath, buffer_id=msg.buffer_id, in_port=msg.in_port,
            actions=actions)
        datapath.send_msg(out)


    def add_flow(self, datapath, in_port, dst, actions):
        ofproto = datapath.ofproto

        match = datapath.ofproto_parser.OFPMatch(
            in_port=in_port, dl_dst=haddr_to_bin(dst))

        mod = datapath.ofproto_parser.OFPFlowMod(
            datapath=datapath, match=match, cookie=0,
            command=ofproto.OFPFC_ADD, idle_timeout=0, hard_timeout=0,
            priority=ofproto.OFP_DEFAULT_PRIORITY,
            flags=ofproto.OFPFF_SEND_FLOW_REM, actions=actions)
        datapath.send_msg(mod)