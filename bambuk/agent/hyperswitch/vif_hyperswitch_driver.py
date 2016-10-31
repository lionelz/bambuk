import abc
import six
import threading

from oslo_config import cfg

from oslo_log import log as logging

from bambuk.agent.hyperswitch import hyperswitch_utils as hu
from bambuk.agent.hyperswitch import vif_hypervm_driver

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller import ofp_handler
from ryu.controller.handler import CONFIG_DISPATCHER
from ryu.controller.handler import MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ipv4
from ryu.ofproto import ether
from ryu.ofproto import inet
from ryu.ofproto import ofproto_v1_3


hyper_swith_agent_opts = [
    cfg.StrOpt('network_mngt_interface',
               default='eth0',
               help='The management network interface'),
    cfg.StrOpt('network_data_interface',
               default='eth1',
               help='The data network interface'),
    cfg.StrOpt('network_vms_interface',
               default='eth2',
               help='the VM network interface'),
    cfg.StrOpt('vpn_bridge_name',
               default='br-vpn',
               help='The VPN bridge name'),
    cfg.StrOpt('eth0_cidr',
               help='eth0 cidr'),
    cfg.StrOpt('eth1_cidr',
               help='eth1 cidr'),
    cfg.StrOpt('eth2_cidr',
               help='eth2 cidr'),
]


cfg.CONF.register_opts(hyper_swith_agent_opts, 'hyperswitch')


LOG = logging.getLogger(__name__)
NIC_NAME_LEN = vif_hypervm_driver.NIC_NAME_LEN


def get_nsize(netmask):
    binary_str = ''
    for octet in netmask.split('.'):
        binary_str += bin(int(octet))[2:].zfill(8)
    return str(len(binary_str.rstrip('0')))


class HyperSwitchVIFDriver(vif_hypervm_driver.AgentVMVIFDriver):
    """VIF driver for hyperswitch networking."""

    def __init__(self, *args, **kwargs):
        super(HyperSwitchVIFDriver, self).__init__(*args, **kwargs)
        self.mgnt_nic = cfg.CONF.hyperagent.network_mngt_interface
        self.vm_nic = cfg.CONF.hyperagent.network_vms_interface
        if self.vm_nic == 'eth0':
            self.vm_cidr = cfg.CONF.hyperagent.eth0_cidr
        if self.vm_nic == 'eth1':
            self.vm_cidr = cfg.CONF.hyperagent.eth1_cidr
        if self.vm_nic == 'eth2':
            self.vm_cidr = cfg.CONF.hyperagent.eth2_cidr
        if not self.vm_cidr or self.vm_cidr.split('/')[0] == '':
            lease_file = '/var/lib/dhcp/dhclient.%s.leases' % self.vm_nic
            mask = None
            ip = None
            with open(lease_file, 'r') as f:
                for line in f:
                    if 'subnet-mask' in line:
                        mask = line.split()[2].split(';')[0]
                    if 'fixed-address' in line:
                        ip = line.split()[1].split(';')[0]
            self.vm_cidr = '%s/%s' % (ip, get_nsize(mask))
        self.br_vpn = cfg.CONF.hyperagent.vpn_bridge_name

    def startup_init(self):
        # plug the agent vm vifs
        super(HyperSwitchVIFDriver, self).startup_init()

        # prepare the VPN bridge

        vm_nic_cidr = self.vm_cidr
        vm_nic_mac = hu.get_mac(self.vm_nic)
        # create the br-vpn bridge
        hu.add_ovs_bridge(self.br_vpn)

        # Set the IP
        hu.execute('ip', 'addr', 'flush', 'dev', self.vm_nic,
                   run_as_root=True)
        hu.execute('ip', 'link', 'set', 'dev', self.vm_nic, 'promisc', 'on',
                   run_as_root=True)
        hu.execute('ip', 'link', 'set', 'dev', self.br_vpn, 'up',
                   run_as_root=True)
        hu.set_mac_ip(self.br_vpn, vm_nic_mac, vm_nic_cidr)

        # add the vm interface to the bridge
        hu.add_ovs_port(self.br_vpn, self.vm_nic)

        # set the controller as local controller
        mgnt_ip = hu.get_nic_cidr(self.mgnt_nic).split('/')[0]
        hu.execute('ovs-vsctl',
                   'set-controller',
                   self.br_vpn,
                   'tcp:%s:6633' % mgnt_ip,
                   run_as_root=True)

        # run the ryu appllication VPNBridgeHandler
        app_mgr = app_manager.AppManager.get_instance()
        self.open_flow_app = app_mgr.instantiate(VPNBridgeHandler,
                                                 vif_hypervm_driver=self)
        self.open_flow_app.start()

    def cleanup(self):
        # remove the br-vpn bridge
        hu.del_ovs_bridge('br-vpn')


class VPNBridgeHandler(ofp_handler.OFPHandler):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(VPNBridgeHandler, self).__init__(*args, **kwargs)
        self._vif_driver = kwargs['vif_hypervm_driver']
        self._drivers = list()
        self._drivers.append(OpenVPNTCP(first_port=1194))
        self._drivers.append(OpenVPNUDP(first_port=1194))
        self.br_vpn = cfg.CONF.hyperagent.vpn_bridge_name

    def mod_flow(self,
                 datapath,
                 cookie=0,
                 cookie_mask=0,
                 idle_timeout=0,
                 match=None,
                 actions=None,
                 priority=0):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        mod = parser.OFPFlowMod(datapath=datapath, cookie=cookie,
                                idle_timeout=idle_timeout,
                                cookie_mask=cookie_mask, priority=priority,
                                match=match, instructions=inst,
                                flags=ofproto.OFPFF_SEND_FLOW_REM)
        datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def _switch_features_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        LOG.info('_switch_features_handler msg= %s' % msg)

        # send to the controller that flows that match the VPN packets
        n = 1
        for driver in self._drivers:
            match = driver.to_controller_match(parser)
            actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                              ofproto.OFPCML_NO_BUFFER)]
            self.mod_flow(datapath=datapath,
                          cookie=n,
                          match=match,
                          actions=actions,
                          priority=10)
            n = n + 1

        # all others => normal linux stack
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_NORMAL)]
        self.mod_flow(datapath=datapath, match=match, actions=actions)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        LOG.info('_packet_in_handler msg= %s' % msg)
        
        # from IP, get hyper_vif / instance data
        pkt = packet.Packet(data=msg.data)
        pkt_ethernet = pkt.get_protocol(ethernet.ethernet)
        pkt_ipv4 = pkt.get_protocol(ipv4.ipv4)
        if not pkt_ethernet or not pkt_ipv4:
            return
        vpn_driver = self._drivers[msg.cookie - 1]
        provider_ip = pkt_ipv4.src
        with LocalLock():
            if vpn_driver.add(provider_ip):
                result = self._vif_driver.call_back.get_vif_for_provider_ip(
                    provider_ip=provider_ip)
                instance_id = result['instance_id']
                hyper_vif = result['hyper_vif']

                # - call plug: create the tap/bridge/...
                LOG.info("hyper_vif=%s" % hyper_vif)
                # - create the bridge/br-int entry....
                vnic = self._vif_driver.create_br_vnic(instance_id, hyper_vif)

                # - start openvpn process for the VM
                vpn_nic_ip = hu.get_nic_cidr(self.br_vpn).split('/')[0]
                vpn_driver.start_vpn(vnic, vpn_nic_ip, hyper_vif['address'])

                # - add the flow for the vpn packet match/action
                match, actions = vpn_driver.intercept_vpn_packets(
                    parser, ofproto, provider_ip)
                # TODO: set to 20 mn
                # - idle_timeout: 30 s for test
                self.mod_flow(datapath=datapath,
                              cookie=msg.cookie,
                              idle_timeout=30,
                              match=match,
                              actions=actions,
                              priority=100)
                match, actions = vpn_driver.return_vpn_packets(
                    parser, ofproto, provider_ip)
                self.mod_flow(datapath=datapath,
                              cookie=msg.cookie,
                              idle_timeout=30,
                              match=match,
                              actions=actions,
                              priority=100)

    @set_ev_cls(ofp_event.EventOFPFlowRemoved, MAIN_DISPATCHER)
    def _flow_removed_handler(self, ev):
        msg = ev.msg
        LOG.info('_flow_removed_handler msg= %s' % msg)
        provider_ip = None
        if 'ipv4_dst' in msg.match:
            provider_ip = msg.match['ipv4_dst']
        if 'ipv4_src' in msg.match:
            provider_ip = msg.match['ipv4_src']
        vpn_driver = self._drivers[msg.cookie - 1]
        if not provider_ip:
            return
        with LocalLock():
            port = vpn_driver.remove(provider_ip)
            if not port:
                return
            result = self._vif_driver.call_back.get_vif_for_provider_ip(
                provider_ip=provider_ip)
            hyper_vif = result['hyper_vif']
            vnic = self._vif_driver.remove_br_vnic(hyper_vif)
            vpn_driver.stop_vpn(vnic)


class LocalLock(object):
    lock = threading.Lock()

    def __enter__(self):
        LocalLock.lock.acquire(True)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        LocalLock.lock.release()


@six.add_metaclass(abc.ABCMeta)
class VPNDriver(object):

    def __init__(self, first_port=1194):
        self.provider_ips = dict()
        self.cur_port = first_port

    def add(self, provider_ip):
        if provider_ip in self.provider_ips:
            return False
        self.cur_port = self.cur_port + 1
        self.provider_ips[provider_ip] = self.cur_port
        return self.cur_port

    def remove(self, provider_ip):
        if provider_ip in self.provider_ips:
            port = self.provider_ips[provider_ip]
            del self.provider_ips[provider_ip]
            return port
        return False

    @abc.abstractmethod
    def to_controller_match(self, parser):
        pass

    @abc.abstractmethod
    def intercept_vpn_packets(self, parser, ofproto, provider_ip):
        pass

    @abc.abstractmethod
    def return_vpn_packets(self, parser, ofproto, provider_ip):
        pass

    @abc.abstractmethod
    def start_vpn(self, vnic, vpn_nic_ip, mac):
        pass

    @abc.abstractmethod
    def stop_vpn(self, vnic):
        pass


class OpenVPNTCP(VPNDriver):

    def __init__(self, first_port=1194):
        super(OpenVPNTCP, self).__init__(first_port)
        self.proto = 'tcp'

    def to_controller_match(self, parser):
        return parser.OFPMatch(eth_type=ether.ETH_TYPE_IP,
                               ip_proto=inet.IPPROTO_TCP,
                               tcp_dst=1194)

    def intercept_vpn_packets(self, parser, ofproto, provider_ip):
        return (parser.OFPMatch(eth_type=ether.ETH_TYPE_IP,
                                ip_proto=inet.IPPROTO_TCP,
                                tcp_dst=1194,
                                ipv4_src=provider_ip),
                [parser.OFPActionSetField(tcp_dst=self.cur_port), 
                 parser.OFPActionOutput(ofproto.OFPP_NORMAL)])

    def return_vpn_packets(self, parser, ofproto, provider_ip):
        return (parser.OFPMatch(eth_type=ether.ETH_TYPE_IP,
                                ip_proto=inet.IPPROTO_TCP,
                                ipv4_dst=provider_ip,
                                tcp_src=self.cur_port),
                [parser.OFPActionSetField(tcp_src=1194), 
                 parser.OFPActionOutput(ofproto.OFPP_NORMAL)])

    def start_vpn(self, vnic, vpn_nic_ip, mac):
        tap = "tap_%s" % vnic
        br = "obr%s" % vnic[3:]
        if not hu.device_exists(tap):
            hu.execute('openvpn', '--mktun', '--dev', tap,
                       check_exit_code=False,
                       run_as_root=True)
        hu.execute('ip', 'link', 'set', 'dev', tap, 'up',
                   run_as_root=True)
        hu.create_linux_bridge(br, [vnic, tap])

        pid = hu.process_exist(['openvpn', tap])
        if pid:
            hu.execute('kill', str(pid), run_as_root=True)

        hu.launch('openvpn',
                  '--local', vpn_nic_ip,
                  '--port', str(self.cur_port),
                  '--proto', self.proto,
                  '--dev', tap,
                  '--ca', '/etc/openvpn/ca.crt',
                  '--cert', '/etc/openvpn/server.crt',
                  '--key', '/etc/openvpn/server.key',
                  '--dh', '/etc/openvpn/dh2048.pem',
                  '--server-bridge',
                  '--keepalive', '10', '120',
                  '--auth', 'none',
                  '--cipher', 'none',
                  '--status', '/var/log/openvpn-status-%s.log' % tap,
                  '--verb', '4',
                  run_as_root=True)

    def stop_vpn(self, vnic):
        tap = "tap_%s" % vnic
        br = "obr%s" % vnic[3:]
        pid = hu.process_exist(['openvpn', tap])
        if pid:
            hu.execute('kill', str(pid), run_as_root=True)
        hu.delete_net_dev(tap)
        hu.delete_linux_bridge(br)


class OpenVPNUDP(OpenVPNTCP):

    def __init__(self, first_port=1194):
        super(OpenVPNUDP, self).__init__(first_port)
        self.proto = 'udp'

    def to_controller_match(self, parser):
        return parser.OFPMatch(eth_type=ether.ETH_TYPE_IP,
                               ip_proto=inet.IPPROTO_UDP,
                               udp_dst=1194)

    def intercept_vpn_packets(self, parser, ofproto, provider_ip):
        return (parser.OFPMatch(eth_type=ether.ETH_TYPE_IP,
                                ip_proto=inet.IPPROTO_UDP,
                                udp_dst=1194,
                                ipv4_src=provider_ip),
                [parser.OFPActionSetField(udp_dst=self.cur_port), 
                 parser.OFPActionOutput(ofproto.OFPP_NORMAL)])

    def return_vpn_packets(self, parser, ofproto, provider_ip):
        return (parser.OFPMatch(eth_type=ether.ETH_TYPE_IP,
                                ip_proto=inet.IPPROTO_UDP,
                                ipv4_dst=provider_ip,
                                udp_src=self.cur_port),
                [parser.OFPActionSetField(udp_src=1194), 
                 parser.OFPActionOutput(ofproto.OFPP_NORMAL)])

