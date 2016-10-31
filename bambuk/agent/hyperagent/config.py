from oslo_config import cfg

from oslo_log import log as logging

from neutron.common import rpc

import oslo_messaging as messaging

from bambuk import version


messaging.set_transport_defaults(control_exchange='hyperswitch')

LOG = logging.getLogger(__name__)

# import the configuration options
cfg.CONF.import_opt('host', 'neutron.common.config')
cfg.CONF.import_opt('root_helper', 'neutron.common.config')
cfg.CONF.import_opt('report_interval', 'neutron.common.config')
cfg.CONF.import_opt('host', 'neutron.common.config')
cfg.CONF.import_opt('ovs_vsctl_timeout', 'neutron.agent.common.ovs_lib')
cfg.CONF.import_opt('network_device_mtu', 'neutron.agent.interface')


def init(args, **kwargs):
    product_name = "bambuk-hyper-switch-agent"
    logging.register_options(cfg.CONF)
    logging.setup(cfg.CONF, product_name)
    cfg.CONF(args=args, project=product_name,
             version='%%(prog)s %s' % version.version_info.release_string(),
             **kwargs)
    rpc.init(cfg.CONF)


def get_root_helper(conf):
    return conf.AGENT.root_helper
