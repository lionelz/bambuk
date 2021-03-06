
import oslo_messaging as messaging

from neutron import manager
from neutron.common import rpc
from neutron.plugins.common import constants as p_const

from bambuk.server import config

from oslo_log import log as logging

LOG = logging.getLogger(__name__)


class HyperswitchCallback(object):
    """
        Processes the rpc call back.
    """

    RPC_API_VERSION = '1.0'

    def __init__(self):
        endpoints = [self]
        target = messaging.Target(topic='hyperswitch-callback',
                                  version='1.0',
                                  exchange='hyperswitch',
                                  server=config.get_host())
        self.server = rpc.get_server(target, endpoints)
        self.server.start()
        self._plugin_property = None
        self._l3_plugin_property = None
        self._hyperswitch_plugin_property = None
        super(HyperswitchCallback, self).__init__()

    @property
    def _plugin(self):
        if self._plugin_property is None:
            self._plugin_property = manager.NeutronManager.get_plugin()
        return self._plugin_property

    @property
    def _l3_plugin(self):
        if self._l3_plugin_property is None:
            self._l3_plugin_property = (
                manager.NeutronManager.get_service_plugins().get(
                    p_const.L3_ROUTER_NAT))
        return self._l3_plugin_property

    @property
    def _hyperswitch_plugin(self):
        if self._hyperswitch_plugin_property is None:
            self._hyperswitch_plugin_property = (
                manager.NeutronManager.get_service_plugins().get(
                    'hyperswitch'))
        return self._hyperswitch_plugin_property

    def get_vif_for_provider_ip(self, context, **kwargs):
        """
            Return a port data from a provider IP.
        """
        provider_ip = kwargs['provider_ip']
        host_id = kwargs['host_id']
        evt = kwargs['evt']
        LOG.debug('get_vif_for_provider_ip %s' % provider_ip)
        
        p_ports = self._hyperswitch_plugin.get_agentlessports(
            context, filters={'private_ip': [provider_ip]})
        LOG.debug('provider ports for %s: %s' % (
            provider_ip, p_ports))
        if len(p_ports) != 1:
            LOG.warn('%d ports for %s' % (len(p_ports), provider_ip))
            return None

        ports = self._plugin.get_ports(context, filters={
            'id': [p_ports[0]['id']]
        })
        LOG.debug('hyper port %s' % ports)
        if len(ports) != 1:
            return None
        port = ports[0]
        if evt == 'up':
            self._plugin.update_port(
                context,
                port['id'],
                {'port': {'binding:host_id': host_id}})
            tenant_id = port['tenant_id']
            LOG.debug('tenant_id: %s' % tenant_id)
            routers = self._l3_plugin.get_routers(
                context,
                filters={'tenant_id': [tenant_id]})
            LOG.debug('routers: %s' % routers)
            for router in routers:
                self._l3_plugin.update_router(
                    context,
                    router['id'],
                    {'router': {'admin_state_up': False}})
                self._l3_plugin.update_router(
                    context,
                    router['id'],
                    {'router': {'admin_state_up': True}})

        return {'device_id': port['device_id'],
                'vif_id': port['id'],
                'mac': port['mac_address']}


class HyperswitchAPI(object):
    """
        Client side of the Hyper Switch RPC API
    """

    def __init__(self):
        target = messaging.Target(topic='hyperswitch-update',
                                  version='1.0',
                                  exchange='hyperswitch')
        self.client = rpc.get_client(target)
        self.call_back = HyperswitchCallback()
        super(HyperswitchAPI, self).__init__()