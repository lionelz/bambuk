from bambuk.agent.hyperswitch import hyperswitch_utils as hu
from bambuk.agent.hyperswitch import vif_driver

from oslo_concurrency import lockutils

from oslo_log import log as logging


LOG = logging.getLogger(__name__)
NIC_NAME_LEN = 14


class AgentVMVIFDriver(vif_driver.HyperVIFDriver):
    """VIF driver for hypervm networking."""

    def __init__(self, *args, **kwargs):
        self.call_back = kwargs.get('call_back')
        self.instance_id = kwargs.get('instance_id')
        super(AgentVMVIFDriver, self).__init__()

    def startup_init(self):
        pass

    def cleanup(self):
        # nothing to do
        pass

    def get_br_name(self, iface_id):
        return ("qbr" + iface_id)[:NIC_NAME_LEN]

    def get_veth_pair_names(self, iface_id):
        return (("qvm%s" % iface_id)[:NIC_NAME_LEN],
                ("qvo%s" % iface_id)[:NIC_NAME_LEN])

    def get_tap_name(self, iface_id):
        return ("tap%s" % iface_id)[:NIC_NAME_LEN]

    def get_veth_pair_names2(self, iface_id):
        return (self.get_tap_name(iface_id),
                ("tvo%s" % iface_id)[:NIC_NAME_LEN])

    def get_bridge_name(self, vif):
        br_int = vif['network']['bridge']
        if br_int:
            return br_int
        return 'br-int'

    def get_ovs_interfaceid(self, vif):
        return vif.get('ovs_interfaceid') or vif.get('id')

    def create_br_vnic(self, instance_id, vif):
        br_name = self.get_br_name(vif.get('id'))
        br_int_veth, qbr_veth = self.get_veth_pair_names(vif.get('id'))
        iface_id = self.get_ovs_interfaceid(vif)

        # veth for br-int creation
        if not hu.device_exists(qbr_veth):
            hu.create_veth_pair(br_int_veth, qbr_veth)

        # add in br-int the veth
        hu.create_ovs_vif_port(self.get_bridge_name(vif),
                               qbr_veth, iface_id,
                               vif['address'], instance_id)

        tap_veth, vnic_veth = self.get_veth_pair_names2(vif.get('id'))
        # veth for virtual nic creation
        if not hu.device_exists(vnic_veth):
            hu.create_veth_pair(tap_veth, vnic_veth)

        # linux bridge creation
        hu.create_linux_bridge(br_name, [br_int_veth, tap_veth])
        return vnic_veth

    def remove_br_vnic(self, vif):
        v1_name, v2_name = self.get_veth_pair_names(vif.get('id'))
        t1_name, t2_name = self.get_veth_pair_names2(vif.get('id'))

        # remove the br-int ports
        hu.delete_ovs_vif_port(self.get_bridge_name(vif), v2_name)

        # remove veths
        hu.delete_net_dev(v1_name)
        hu.delete_net_dev(v2_name)
        hu.delete_net_dev(t1_name)
        hu.delete_net_dev(t2_name)

        # remove linux bridge
        br_name = self.get_br_name(vif.get('id'))
        hu.delete_linux_bridge(br_name)
        return t2_name

    @lockutils.synchronized('hypervm-plug-unplug')
    def plug(self, instance_id, hyper_vif):
        LOG.debug("hyper_vif=%s" % hyper_vif)
        vnic_veth = self.create_br_vnic(instance_id, hyper_vif)
        for subnet in hyper_vif['network']['subnets']:
            LOG.debug("subnet: %s" % subnet)
            if subnet['version'] == 4:
                # set the IP/mac on the vnic
                h_cidr = subnet['cidr']
                h_ip = subnet['ips'][0]['address']
                h_cidr_ip = h_ip + '/' + h_cidr.split('/')[1]
                hu.set_mac_ip(vnic_veth, hyper_vif['address'], h_cidr_ip)
                # set the default route
                h_gw = None
                if subnet.get('gateway'):
                    h_gw = subnet['gateway'].get('address')
                    if h_gw:
                        # TODO: how to choose the good gateway????
                        # remove default route
                        hu.execute('ip', 'route', 'del', '0/0',
                                   check_exit_code=False,
                                   run_as_root=True)
                        hu.execute('ip', 'route', 'add', 'default',
                                   'via', h_gw,
                                   run_as_root=True)
        # set MTU
        hu.set_device_mtu(vnic_veth, 1400)

    @lockutils.synchronized('hypervm-plug-unplug')
    def unplug(self, hyper_vif):
        LOG.debug("unplug=%s" % hyper_vif)
        self.remove_br_vnic(hyper_vif)
