
import oslo_messaging as messaging

from neutron import manager

from oslo_config import cfg

from oslo_log import log as logging

from neutron.common import rpc

LOG = logging.getLogger(__name__)


class HyperSwitchCallback(object):
    """
        Processes the rpc call back.
    """

    RPC_API_VERSION = '1.0'

    def __init__(self):
        endpoints = [self]
        target = messaging.Target(topic='hyperswitch-callback',
                                  version='1.0',
                                  exchange='hyperswitch',
                                  server=cfg.CONF.host)
        self.server = rpc.get_server(target, endpoints)
        self.server.start()
        super(HyperSwitchCallback, self).__init__()

    @property
    def _plugin(self):
        if self._plugin_property is None:
            self._plugin_property = manager.NeutronManager.get_plugin()
        return self._plugin_property


    def get_vif_for_provider_ip(self, context, **kwargs):
        """
            Return a port data from a provider IP.
        """
        provider_ip = kwargs['provider_ip']
        p_ports = self._plugin.get_ports(context, filters={
            'fixed-ips': {
                'ip_address': [provider_ip]
            }})
        if len(p_ports) != 1:
            return None

        ports = self._plugin.get_ports(context, filters={
            'fixed-ips': {
                'ip_address': p_ports
            }})
        if len(ports) != 1:
            return None
        port = ports[0]
        return {'instance_id': port['device_id'], 'mac': port['address']}


class HyperSwitchAPI(object):
    """
        Client side of the Hyper Switch RPC API
    """

    def __init__(self):
        target = messaging.Target(topic='hyperswitch-update',
                                  version='1.0',
                                  exchange='hyperswitch')
        self.client = rpc.get_client(target)
        self.call_back = HyperSwitchCallback()
        super(HyperSwitchAPI, self).__init__()
