from pox.misc.loadbalancing.base.iplb_base import log, str_to_dpid, IPAddr, core

# Remember which DPID we're operating on (first one to connect)
_dpid = None


def launch_base(ip, servers, class_name, class_def, dpid=None):
    """Serves as a base for the launch function present in every load balancing class file.
    This is meant to make the code less WET and more DRY.

    :param ip: ip of load balancing server. Given via command line
    :param servers: ips of hosts. Given via command line
    :param class_name: string "iplb"
    :param class_def: points to definition of load balancing class
    :param dpid: optional command line argument
    :return:
    """
    global _dpid
    if dpid is not None:
        _dpid = str_to_dpid(dpid)

    servers = servers.replace(",", " ").split()
    servers = [IPAddr(x) for x in servers]
    ip = IPAddr(ip)

    # We only want to enable ARP Responder *only* on the load balancer switch,
    # so we do some disgusting hackery and then boot it up.
    from proto.arp_responder import ARPResponder
    old_pi = ARPResponder._handle_PacketIn

    def new_pi(self, event):
        if event.dpid == _dpid:
            # Yes, the packet-in is on the right switch
            return old_pi(self, event)

    ARPResponder._handle_PacketIn = new_pi

    # Hackery done.  Now start it.
    from proto.arp_responder import launch as arp_launch
    arp_launch(eat_packets=False, **{str(ip): True})
    import logging
    logging.getLogger("proto.arp_responder").setLevel(logging.WARN)

    def _handle_ConnectionUp(event):
        global _dpid
        if _dpid is None:
            _dpid = event.dpid

        if _dpid != event.dpid:
            log.warn("Ignoring switch %s", event.connection)
        else:
            if not core.hasComponent(class_name):
                # Need to initialize first...
                core.registerNew(class_def, event.connection, IPAddr(ip), servers)
                log.info("Load Balancer Ready.")
            log.info("Load Balancing on %s", event.connection)

            # Gross hack
            core.class_def.con = event.connection
            event.connection.addListeners(core.class_def)

    core.openflow.addListenerByName("ConnectionUp", _handle_ConnectionUp)
