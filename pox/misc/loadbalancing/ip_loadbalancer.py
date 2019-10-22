from pox.misc.loadbalancing.base.iplb_base import *
from pox.misc.loadbalancing.base.launch_base import launch_base


class iplb(iplb_base):
    def _pick_server(self, key, inport):
        """Randomly picks a server to 'balance the load' """
        self.log.info('Using random choice load balancing algorithm.')
        return random.choice(self.live_servers.keys())


def launch(ip, servers, dpid=None):
    return launch_base(ip, servers, 'iplb', iplb, dpid)
