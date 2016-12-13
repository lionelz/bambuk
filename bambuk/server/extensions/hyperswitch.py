import abc

from neutron.api import extensions
from neutron.api.v2 import resource_helper


RESOURCE_ATTRIBUTE_MAP = {
    'agentless_ports': {
        'port_id': {'allow_post': True, 'allow_put': True,
                    'is_visible': True},
    },
    'hyperswitchs': {
        'flavor': {'allow_post': True, 'allow_put': False,
                          'is_visible': True},
        'vm_id': {'allow_post': True, 'allow_put': False,
                  'is_visible': True, 'default': None},
        'tenant_id': {'allow_post': True, 'allow_put': False,
                      'is_visible': True},
    },
}


class Hyperswitch(extensions.ExtensionDescriptor):

    """API extension for Hyperswitch."""

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


class HyperswitchPluginBase(object):

    @abc.abstractmethod
    def create_agentless_port(self, context, agentless_port):
        pass

    @abc.abstractmethod
    def get_agentless_port(self, context, agentless_port_id, fields=None):
        pass

    @abc.abstractmethod
    def delete_agentless_port(self, context, agentless_port_id):
        pass

    @abc.abstractmethod
    def get_agentless_ports(self, context, filters=None, fields=None,
                            sorts=None, limit=None, marker=None,
                            page_reverse=False):
        pass

    @abc.abstractmethod
    def create_hyperswitch(self, context, hyperswitch):
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
    def get_hyperswitch_host_name(self,
                                  hybrid_cloud_vm_id=None,
                                  hybrid_cloud_tenant_id=None):
        pass

    @abc.abstractmethod
    def launch_hyperswitch(self,
                           user_data,
                           flavor,
                           net_list,
                           hybrid_cloud_vm_id=None,
                           hybrid_cloud_tenant_id=None):
        pass
