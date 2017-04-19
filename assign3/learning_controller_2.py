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


# Generates the edges of the minimum spanning tree through Prim's algorithm.
# Portions of code borrowed from NetworkX documentation.
def get_edges(graph):
    unvisited_nodes = graph.nodes()
    while unvisited_nodes:
        u = unvisited_nodes.pop(0)
        neighbors = []
        visited_nodes = []
        for u, v in graph.edges(u):
            neighbors.append((u, v))
        while neighbors:
            (u, v) = neighbors.pop(0)
            if v in visited_nodes:
                continue
            visited_nodes.append(v)
            try:
                unvisited_nodes.remove(v)
            except:
                pass
            for v, w in graph.edges(v):
                if w not in visited_nodes:
                    neighbors.append((v, w))
            yield (u, v)


# This function takes as input a networkx graph. It then computes
# the minimum Spanning Tree, and returns it, as a networkx graph.
# Uses the subroutine get_edges(graph) to generate the edges of the minimum spanning tree
# via Prim's algorithm, then checks to see if all of the nodes are present.
# Then it copies all of the data associated with the nodes ('ports', 'mactoport') and returns the
# new spanning tree.
# Portions of code borrowed from NetworkX documentation.
def compute_spanning_tree(G):
    # The Spanning Tree of G.
    edges = get_edges(G)
    ST = nx.Graph(edges)
    if len(ST) != len(G):
        ST.add_nodes_from([n for n, d in G.degree().items() if d == 0])

    # Copy over the relevant ports.
    for n in ST:
        ST.node[n]['ports'] = {}
        for machine, port in G.node[n]['ports'].items():
            if machine != 'host':
                edges = []
                for edge in ST[n]:
                    edges.append(edge)
                if int(machine) in edges:
                    ST.node[n]['ports'][machine] = port
            elif machine == 'host':
                ST.node[n]['ports'][machine] = port
    ST.graph = G.graph.copy()
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
            return

    # Grab the MAC addresses of the source and destination.
        dst = eth.dst
        src = eth.src
        print '\n\n'
        print '/////////////// MACHINE ' + str(dpid) + ' ///////////////'


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

    # Check if the destination is in the node's MAC address dictionary.
        if dst in self.G.node[dpid]['mactoport']:
            out_port =  self.G.node[dpid]['mactoport'][dst]
            print('Entry exists', str(out_port), 'from', dpid)
            actions = [datapath.ofproto_parser.OFPActionOutput(out_port)]

    # Add a flow.
            self.add_flow(datapath, msg.in_port, dst, actions)

            out = datapath.ofproto_parser.OFPPacketOut(
                datapath=datapath, buffer_id=msg.buffer_id, in_port=msg.in_port,
                actions=actions, data=data)

            datapath.send_msg(out)
        else:
    # Flood the neighbors of the Spanning Tree.
            print '\nNo entry of ' + dst + ' on ' + str(dpid) + ', flooding network'
            print self.ST.node[dpid]['ports']
            #neighbors = nx.get_node_attributes(self.ST, 'ports')
            #print neighbors

            #  out_port = ofproto.OFPP_FLOOD
            '''
            actions = [datapath.ofproto_parser.OFPActionOutput(self.ST.node[dpid]['ports']['host'])]
            print 'sending to ' + str(self.ST.node[dpid]['ports']['host'])
            out = datapath.ofproto_parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id, in_port=msg.in_port, actions=actions, data=data)


            datapath.send_msg(out)
            '''
            print 'iterating over above dict, sending to each neighbor'
            for machine, port in self.ST.node[dpid]['ports'].items():
                if msg.in_port != port:
                    print 'sending to machine ' + machine + ' over port ' + str(port)
                    actions = [datapath.ofproto_parser.OFPActionOutput(port)]
                    out = datapath.ofproto_parser.OFPPacketOut(
                        datapath=datapath, buffer_id=msg.buffer_id, in_port=msg.in_port,
                        actions=actions, data=data)
                    datapath.send_msg(out)
                else:
                    print 'not sending back to the sender'
            print 'done with for loop'




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