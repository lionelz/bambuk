
from bambuk.server import hyper_switch_api
from bambuk.server.extensions import hyperswitch
from bambuk.server.extensions.aws import aws_impl

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
    cfg.DictOpt('aws_flavor_map',
                default={'0G': 't2.micro',
                         '1G': 'c4.large',
                         '10G': 'c4.xlarge'},
                help=_("AWS flavor Map")),
]

cfg.CONF.register_opts(OPTS_HYPERSWITCH, 'HYPERSWITCH')


class HyperSwitchPlugin(hyperswitch.HyperSwitchPluginBase):
    
    def __init__(self):
        # TODO: instantiate aws or hec driver
        self._provider_impl = aws_impl.AWSProvider()
        self._hyper_switch_api = hyper_switch_api.HyperSwitchAPI()
        

    def create_agentless(self, context, port_id):
        # TODO:
        #   - create a provider port with the name port_id
        #   - 
        self._provider_impl.create_port()
        pass

    def get_agentless(self, context, port_id, fields=None):
        pass

    def delete_agentless(self, context, port_id):
        pass

    def get_agentlesss(self, context, filters=None, fields=None,
                       sorts=None, limit=None, marker=None,
                       page_reverse=False):
        # TODO: filter by port_id and provider_ip
        pass

    def create_hyperswitch(self, context, hyperswitch):
        user_data = ('rabbit_userid=stackrabbit' +
                     'rabbit_password=stack' +
                     'rabbit_hosts=172.31.152.16' +
                     'host=tenant-xxx-1' +
                     'host=vm-xxx-1' +
                     'network_mngt_interface=eth0' +
                     'network_data_interface=eth1' +
                     'network_vms_interface=eth2')

        net_list = []
        self._provider_impl.launch_vm(
            hyperswitch['flavor'],
            hyperswitch['vm_id'],
            hyperswitch['tenant_id'],
            user_data,
            net_list
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

