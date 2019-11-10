from pox.misc.loadbalancing.base.lblc_base import *


class iplb(lblc_base):

    def __init__(self, server, first_packet, client_port):
        """Extend the __init__ function with extra fields"""
        super(iplb, self).__init__(server, first_packet, client_port)

        # create dictionary to show each server's weight
        # NOTE: Since each node is virtual, they will all have the same weight 1.
        #       Also, since weight represents a node's hardware capability, it is immutable.
        self.server_weight = {k: 1 for k in self.servers}
        self.log.debug('Server Weights: {}'.format(self.server_weight))

    def _pick_server (self,key,inport):
        self.log.info('Using Weighted Round Robin load balancing algorithm.')

        if not bool(self.live_servers):
            self.log.error('Error: No servers are online!')
            return



        """
        pick the server with the highest weight value (most capable of handling the new connection).
        """

        servers = self.servers

        # slice the self.server_weight dictionary to only have minimally loaded servers
        weight_sliced = {k: v for k, v in self.server_weight.items() if k in servers}



        server = max(weight_sliced, key=weight_sliced.get)

        self._mutate_server_load(server, 'inc')

        return server


# Remember which DPID we're operating on (first one to connect)
_dpid = None


def launch(ip, servers, dpid=None):
    global _dpid
    if dpid is not None:
        _dpid = str_to_dpid(dpid)

    servers = servers.replace(",", " ").split()
    servers = [IPAddr(x) for x in servers]
    ip = IPAddr(ip)

    # We only want to enable ARP Responder *only* on the load balancer switch,
    # so we do some disgusting hackery and then boot it up.
    from proto.arp_responder import ARPResponder
