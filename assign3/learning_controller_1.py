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

        print nx.get_node_attributes(self.ST, 'ports')
        print nx.get_node_attributes(self.G, 'ports')
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


    # This is the ID of the current node we are on.
        dpid = datapath.id

    # Getting the IP addresses of the source and destination through the ethernet header.
        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)

    # Ignore LLDP packet types.
        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            print 'LLDP ignored.'
            return


    # Grab the MAC addresses of the source and destination.
        dst = eth.dst
        src = eth.src

        print '\n\n/////////////// MACHINE ' + str(dpid) + ' ///////////////'
        print 'SOURCE: ' + src
        print 'DEST  : ' + dst

    # Associate the source MAC address with the port number we received the message from.
        # if src not in self.G.node[dpid]['mactoport']:
        self.G.node[dpid]['mactoport'][src] = msg.in_port
        print 'Added port ' + str(msg.in_port) + ' on machine ' + str(dpid)
        print self.get_str_mactoport(self.G, dpid)

    # If there is no buffer then set the data variable.
    # Otherwise we want a null data variable.
        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data


    # Declare an empty actions list to append ports to.
        actions = []
    # Check if the destination is in the node's MAC address dictionary.
        if dst in self.G.node[dpid]['mactoport']:
            out_port =  self.G.node[dpid]['mactoport'][dst]
            print 'Entry exists for port ' + str(out_port)
            actions.append(datapath.ofproto_parser.OFPActionOutput(out_port))
    # Add a flow.
            self.add_flow(datapath, msg.in_port, dst, actions)

            out = datapath.ofproto_parser.OFPPacketOut(
                datapath=datapath, buffer_id=msg.buffer_id, in_port=msg.in_port,
                actions=actions)

            datapath.send_msg(out)

    # Flood the neighbors of the Spanning Tree.
        else:
            print '\nNo entry of ' + dst + ' on ' + str(dpid) + ', flooding network'
            #print self.ST.node[dpid]['ports']
            #print nx.get_node_attributes(self.ST, 'ports')[dpid]
            #print nx.get_node_attributes(self.G,  'ports')[dpid]
            #print neighbors

            #  out_port = ofproto.OFPP_FLOOD

            print 'iterating over above dict, sending to each neighbor\nneighbors:'
            neighbors = self.get_ST_neighbors(self.ST, dpid)
            print neighbors
            for machine in neighbors:
                if machine != 'host':
                    port = self.ST.node[dpid]['ports'][machine]
                    if msg.in_port != port:
                        print 'Sending to machine ' + machine + ' over port ' + str(port)
                        actions.append(datapath.ofproto_parser.OFPActionOutput(port))
                    else:
                        print 'Not sending back to the sender, machine ' + machine

            print 'Done with for loop, sending out'
            actions.append(datapath.ofproto_parser.OFPActionOutput(self.ST.node[dpid]['ports']['host']))
            out = datapath.ofproto_parser.OFPPacketOut(
                datapath=datapath, buffer_id=msg.buffer_id,
                in_port=msg.in_port, actions=actions
            )
            datapath.send_msg(out)


    def get_ST_neighbors(self, graph, dpid):
        neighbors = []
        for (u, v) in graph.edges():
            if u == dpid or v == dpid:
                if u == dpid:
                    neighbors.append(str(v))
                else:
                    neighbors.append(str(u))
        neighbors.append('host')
        return neighbors

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