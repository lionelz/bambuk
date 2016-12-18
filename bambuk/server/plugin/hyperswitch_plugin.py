
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
        # TODO: create security groups for HSs and VMs
        self._security_groups = [
            config.get_data_security_group(),
            config.get_data_security_group(),
            config.get_data_security_group()
        ]

    @property
    def _core_plugin(self):
        return manager.NeutronManager.get_plugin()

    def get_plugin_type(self):
        """Get type of the plugin."""
        return "hyperswitch"

    def get_plugin_description(self):
        """Get description of the plugin."""
        return "Hyperswitch Management Plugin"

    def create_agentlessport(self, context, agentlessport):
        #   - create a provider port with the name port_id
        port = agentlessport['agentlessport']
        port_id = port.get('port_id')
        indice = port.get('indice')
        vm_id = port.get('vm_id')
        tenant_id = port.get('tenant_id')
        flavor = port.get('flavor')
        if not flavor:
            flavor = config.get_default_flavor()
        net_inf = self._provider_impl.create_network_interface(
            port_id,
            vm_id,
            tenant_id,
            indice,
            self._vms_subnets[indice],
            self._security_groups[indice])
        #   - retrieve the list of hyperswitch
        if config.get_level() == 'vm':
            hss = self._provider_impl.get_hyperswitchs(
                vm_ids=[vm_id])
            if not hss or len(hss) == 0:
                hss = self.create_hyperswitch(context, {
                    'hyperswitch': {
                        'vm_id': vm_id,
                        'flavor': flavor
                    }
                })
        else:
            hss = self._provider_impl.get_hyperswitchs(
                tenant_ids=[tenant_id])
            if not hss or len(hss) == 0:
                hss = self.create_hyperswitch(context, {
                    'hyperswitch': {
                        'tenant_id': tenant_id,
                        'flavor': flavor
                    }
                })
        hsservers_ip = None
        for hs in hss:
            if hsservers_ip:
                hsservers_ip = ', %s' % hs['private_ip']
            else:
                hsservers_ip = '%s' % hs['private_ip']
        return {
            'id': port_id,
            'indice': indice,
            'vm_id': vm_id,
            'tenant_id': tenant_id,
            'flavor': flavor,
            'user_data': {
                'mac%d' % indice: net_inf['mac'],
                'hsservers%d' % indice: hsservers_ip
            } 
        }

    def get_agentlessport(self, context, agentlessport_id, fields=None):
        LOG.debug('get agentless port %s.' % agentlessport_id)
        return self._provider_impl.get_network_interfaces(
            agentlessport_id)[0]

    def delete_agentlessport(self, context, agentlessport_id):
        LOG.debug('removing agentless port %s.' % agentlessport_id)
        self._provider_impl.delete_network_interface(agentlessport_id)

    def get_agentlessports(self, context, filters=None, fields=None,
                            sorts=None, limit=None, marker=None,
                            page_reverse=False):
        LOG.debug('get agentless ports %s.' % filters)
        if not filters:
            filters = {}
        return self._provider_impl.get_network_interfaces(
            filters.get('name'),
            filters.get('port_id'),
            filters.get('vm_id'),
            filters.get('private_ip'),
            filters.get('tenant_id'),
            filters.get('indice')
        )

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
        # TODO: use security groups for HSs and VMs
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
        agents = self._core_plugin.get_agents(
            context,
            filters={'host': [hyperswitch_id]})
        LOG.debug('agents to delete: %s' % agents)
        for agent in agents:
            self._core_plugin.delete_agent(context, agent.get('id'))

    def get_hyperswitchs(self, context, filters=None, fields=None,
                         sorts=None, limit=None, marker=None,
                         page_reverse=False):
        LOG.debug('get hyperswitch %s.' % filters)
        if not filters:
            filters = {}
        return self._provider_impl.get_hyperswitchs(
            filters.get('name'),
            filters.get('id'),
            filters.get('tenant_id'),
            filters.get('vm_id')
        )

