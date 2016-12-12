from oslo_config import cfg

from oslo_log import log as logging

from neutron.common import rpc

import oslo_messaging as messaging

from bambuk import version

messaging.set_transport_defaults(control_exchange='hyperswitch')

LOG = logging.getLogger(__name__)


# import the configuration options
cfg.CONF.import_opt('host', 'neutron.common.config')
cfg.CONF.import_opt('ovs_vsctl_timeout', 'neutron.agent.common.ovs_lib')


OPTS = [
    cfg.IntOpt('network_device_mtu',
               help=_('MTU setting for device. This option will be removed in '
                      'Newton. Please use the system-wide segment_mtu setting '
                      'which the agents will take into account when wiring '
                      'VIFs.')),
    cfg.StrOpt('rootwrap_config',
               default="/etc/hyperswitch/rootwrap.conf",
               help='Path to the rootwrap configuration file to use for '
                    'running commands as root'),
]
cfg.CONF.register_opts(OPTS)
OPTS_AGENT = [
    cfg.StrOpt('root_helper', default='sudo',
               help=_("Root helper application. "
                      "Use 'sudo bambuk-rootwrap /etc/bambuk/rootwrap.conf' "
                      "to use the real root filter facility. Change to 'sudo' "
                      "to skip the filtering and just run the command "
                      "directly.")),
]
cfg.CONF.register_opts(OPTS_AGENT, 'AGENT')


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
