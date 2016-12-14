
from bambuk.server import config
from bambuk.server import hyper_switch_api
from bambuk.server.aws import aws_impl
from bambuk.server.extensions import hyperswitch

from neutron import manager

from oslo_log import log as logging


LOG = logging.getLogger(__name__)


class HyperswitchPlugin(hyperswitch.HyperswitchPluginBase):

    supported_extension_aliases = ["hyperswitch"]
    
    def __init__(self):
        if config.get_provider() == 'aws':
            self._provider_impl = aws_impl.AWSProvider()
        if config.get_provider() == 'hec':
            self._provider_impl = None
        self._hyper_switch_api = hyper_switch_api.HyperswitchAPI()
        self._vms_subnets = self._provider_impl.get_vms_subnet()
        
    @property
    def _core_plugin(self):
        return manager.NeutronManager.get_plugin()

    def get_plugin_type(self):
        """Get type of the plugin."""
        return "hyperswitch"

    def get_plugin_description(self):
        """Get description of the plugin."""
        return "Hyperswitch Management Plugin"

    def create_agentless_port(self, context, agentless_port):
        # TODO:
        #   - create a provider port with the name port_id
        #   - 
        self._provider_impl.create_port()
        pass

    def get_agentless_port(self, context, agentless_port_id, fields=None):
        pass

    def delete_agentless_port(self, context, agentless_port_id):
        pass

    def get_agentless_ports(self, context, filters=None, fields=None,
                            sorts=None, limit=None, marker=None,
                            page_reverse=False):
        # TODO: filter by port_id and provider_ip
        pass

    def create_hyperswitch(self, context, hyperswitch):
        LOG.debug('hyperswitch %s to create.' % hyperswitch)
        hyperswitch = hyperswitch['hyperswitch']
        rabbit_hosts = None
        for rabbit_host in config.get_rabbit_hosts():
            if rabbit_hosts:
                rabbit_hosts = '%s, %s' % (rabbit_hosts, rabbit_host)
            else:
                rabbit_hosts = rabbit_host
        host = self._provider_impl.get_hyperswitch_host_name(
            hyperswitch.get('vm_id'),
            hyperswitch.get('tenant_id'))
        user_data = {
            'rabbit_userid': config.get_rabbit_userid(),
            'rabbit_password': config.get_rabbit_password(),
            'rabbit_hosts': rabbit_hosts,
            'host': host,
            'network_mngt_interface': 'eth0',
            'network_data_interface': 'eth1',
            'network_vms_interface': 'eth2',
        }

        net_list = [
            {
                'name': config.get_mgnt_network(),
                'security_group': config.get_mgnt_security_group()},
            {
                'name': config.get_data_network(),
                'security_group': config.get_data_security_group()},
        ]
        # TODO: create and use security groups for HSs and VMs
        for vm_subnet in self._vms_subnets:
            net_list.append(
                {
                    'name': vm_subnet,
                    'security_group': config.get_data_security_group()
                }
            )
        hs = self._provider_impl.launch_hyperswitch(
            user_data,
            hyperswitch['flavor'],
            net_list,
            hyperswitch.get('vm_id'),
            hyperswitch.get('tenant_id'),
        )
        LOG.debug('hyperswitch %s created.' % hs)
        return hs

    def get_hyperswitch(self, context, hyperswitch_id, fields=None):
        LOG.debug('hyperswitch %s to show.' % hyperswitch_id)
        hs = self._provider_impl.get_hyperswitchs(
            [hyperswitch_id]
        )
        LOG.debug('%d hyperswitch found for %s: %s.' % (
            len(hs), hyperswitch_id, hs))
        if len(hs) > 0:
            return hs[0]
        else:
            return None

    def delete_hyperswitch(self, context, hyperswitch_id):
        LOG.debug('hyperswitch %s to delete.' % hyperswitch_id)
        self._provider_impl.delete_hyperswitch(hyperswitch_id)
        # TODO: remove the agents 

    def get_hyperswitchs(self, context, filters=None, fields=None,
                         sorts=None, limit=None, marker=None,
                         page_reverse=False):
        LOG.debug('get hyperswitch %s.' % filters)
        if not filters:
            filters = {}
        return self._provider_impl.get_hyperswitchs(
            filters.get('id'),
            filters.get('tenant_id'),
            filters.get('vm_id')
        )

