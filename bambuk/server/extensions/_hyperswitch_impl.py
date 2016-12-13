
from bambuk.server import hyper_switch_api
from bambuk.server.extensions import hyperswitch
from bambuk.server.extensions.aws import aws_impl

from neutron import manager

from oslo_config import cfg


class HyperswitchPlugin(hyperswitch.HyperswitchPluginBase):

    supported_extension_aliases = ["hyperswitch"]
    
    def __init__(self):
        # TODO: instantiate aws or hec driver
        self._provider_impl = aws_impl.AWSProvider()
        self._hyper_switch_api = hyper_switch_api.HyperswitchAPI()
        
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
        rabbit_hosts = None
        for rabbit_host in cfg.CONF.oslo_messaging_rabbit.rabbit_hosts:
            if rabbit_hosts:
                rabbit_hosts = '%s, %s' % (rabbit_hosts, rabbit_host)
            else:
                rabbit_hosts = rabbit_host
        host = self._provider_impl.get_hyperswitch_host_name(
            hyperswitch.get('vm_id'),
            hyperswitch.get('tenant_id'))
        user_data = {
            'rabbit_userid': cfg.CONF.oslo_messaging_rabbit.rabbit_userid,
            'rabbit_password': cfg.CONF.oslo_messaging_rabbit.rabbit_password,
            'rabbit_hosts': rabbit_hosts,
            'host': host,
            'network_mngt_interface': 'eth0',
            'network_data_interface': 'eth1',
            'network_vms_interface': 'eth2',
        }

        #TODO: populate net_list
        net_list = []
        self._provider_impl.launch_hyperswitch(
            user_data,
            hyperswitch['flavor'],
            net_list,
            hyperswitch.get('vm_id'),
            hyperswitch.get('tenant_id'),
        )
        pass

    def get_hyperswitch(self, context, hyperswitch_id, fields=None):
        pass

    def delete_hyperswitch(self, context, hyperswitch_id):
        pass

    def get_hyperswitchs(self, context, filters=None, fields=None,
                         sorts=None, limit=None, marker=None,
                         page_reverse=False):
        pass

