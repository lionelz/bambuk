
import abc

from neutron.api import extensions
from neutron.api.v2 import resource_helper

from oslo_config import cfg


OPTS_HYPERSWITCH = [
    cfg.StrOpt('provider', default='aws',
               help=_("Provider: aws|hec.")),
    cfg.StrOpt('level', default='tenant',
               help=_("Level: tenant|vm.")),
    cfg.StrOpt('mgnt_network',
               help=_("Management network id or name.")),
    cfg.StrOpt('mgnt_security_group',
               help=_("Management network security group id or name.")),
    cfg.StrOpt('data_network',
               help=_("Data network id or name.")),
    cfg.StrOpt('data_security_group',
               help=_("Data network security group id or name.")),
    cfg.ListOpt('vms_cidr', default=['172.31.300.0/24', '172.31.310.0/24'],
               help=_("Data network security group id or name.")),
    cfg.StrOpt('default_flavor', default='1G',
               help=_("Default flavor for hyperswitch creation.")),
    cfg.StrOpt('aws_access_key_id',
               help=_("AWS Access Key Id.")),
    cfg.StrOpt('aws_secret_access_key',
               help=_("AWS Secret Access Key.")),
    cfg.StrOpt('aws_region_name',
               help=_("AWS Region Name.")),
    cfg.DictOpt('aws_flavor_map',
                default={'0G': 't2.micro',
                         '1G': 'c4.large',
                         '10G': 'c4.xlarge'},
                help=_("AWS flavor Map")),
]


cfg.CONF.register_opts(OPTS_HYPERSWITCH, 'hyperswitch')


RESOURCE_ATTRIBUTE_MAP = {
    'agentless_ports': {
        'port_id': {'allow_post': True, 'allow_put': True,
                    'is_visible': True},
    },
    'hyperswitchs': {
        'flavor': {'allow_post': True, 'allow_put': False,
                          'is_visible': True},
        'vm_id': {'allow_post': True, 'allow_put': False,
                  'is_visible': True, 'required_by_policy': False},
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
