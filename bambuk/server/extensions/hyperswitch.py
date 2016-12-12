
import abc

from neutron.api import extensions
from neutron.api.v2 import resource_helper

from bambuk.server import extensions as bambuk_extensions

RESOURCE_ATTRIBUTE_MAP = {
    'agentless': {
        'port_id': {'allow_post': True, 'allow_put': True,
                    'is_visible': True},
    },
    'hyperswitch': {
        'flavor': {'allow_post': True, 'allow_put': False,
                          'is_visible': True},
        'vm_id': {'allow_post': True, 'allow_put': False,
                  'is_visible': True},
        'tenant_id': {'allow_post': True, 'allow_put': False,
                      'is_visible': True},
    },
}


extensions.append_api_extensions_path(bambuk_extensions.__path__)


class HyperSwitch(extensions.ExtensionDescriptor):

    """API extension for HyperSwitch."""

    @classmethod
    def get_name(cls):
        return 'Hyper Switch'

    @classmethod
    def get_alias(cls):
        return 'hyperswitch'

    @classmethod
    def get_description(cls):
        return "Hyper Switch Management."

    @classmethod
    def get_updated(cls):
        return '2016-12-01T00:00:00-00:00'

    @classmethod
    def get_resources(cls):
        """Returns Ext Resources."""
        plural_mappings = resource_helper.build_plural_mappings(
            {}, RESOURCE_ATTRIBUTE_MAP)
        resources = resource_helper.build_resource_info(plural_mappings,
                                                        RESOURCE_ATTRIBUTE_MAP,
                                                        'hyperswitch')

        return resources

    def get_extended_resources(self, version):
        if version == "2.0":
            return RESOURCE_ATTRIBUTE_MAP
        else:
            return {}


class HyperSwitchPluginBase(object):

    @abc.abstractmethod
    def create_agentless(self, context, port_id):
        pass

    @abc.abstractmethod
    def get_agentless(self, context, port_id, fields=None):
        pass

    @abc.abstractmethod
    def delete_agentless(self, context, port_id):
        pass

    @abc.abstractmethod
    def get_agentlesss(self, context, filters=None, fields=None,
                       sorts=None, limit=None, marker=None,
                       page_reverse=False):
        pass

    @abc.abstractmethod
    def create_hyperswitch(self, context, hyperswitch):
#user_data,

# rabbit_userid=stackrabbit
# rabbit_password=stack
# rabbit_hosts=172.31.152.16
# host=tenant-xxx-1
# host=vm-xxx-1
# network_mngt_interface=eth0
# network_data_interface=eth1
# network_vms_interface=eth2

#net_list,

        pass

    @abc.abstractmethod
    def get_hyperswitch(self, context, hyperswitch_id, fields=None):
        # hyperswitch_id = host
        
        # return:
        # host, user_data, tenant_id, vm_id, list of ports (from agent)
        pass

    @abc.abstractmethod
    def delete_hyperswitch(self, context, hyperswitch_id):
        # hyperswitch_id = host
        pass

    @abc.abstractmethod
    def get_hyperswitchs(self, context, filters=None, fields=None,
                         sorts=None, limit=None, marker=None,
                         page_reverse=False):
        # filters
        # host, vm_id, tenant_id
        pass


class ProviderDriver(object):

    @abc.abstractmethod
    def create_port(self):
        pass

    @abc.abstractmethod
    def search_port(self, provider_ip):
        pass

    @abc.abstractmethod
    def launch_vm(self, image_id, flavor):
        pass