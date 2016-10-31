import sys

import eventlet
from agent.hyperswitch import vif_hyperswitch_driver
eventlet.monkey_patch()

import oslo_messaging as messaging

from bambuk.agent.hyperswitch import config

from oslo_config import cfg

from oslo_log import log as logging

from oslo_utils import importutils

from neutron import context
from neutron.common import rpc
from neutron.i18n import _LI


LOG = logging.getLogger(__name__)


class HyperSwitchAgentCallback(object):
    """Processes the rpc call back."""

    RPC_API_VERSION = '1.0'

    def __init__(self):
        target = messaging.Target(topic='hyperswitch-callback',
                                  version='1.0',
                                  exchange='hyperswitch')
        self.client = rpc.get_client(target)
        self.context = context.get_admin_context()
        super(HyperSwitchAgentCallback, self).__init__()

    def get_vif_for_provider_ip(self, provider_ip):
        """Retrieve the VIFs for a provider IP."""
        return self.client.call(self.context, 'get_vif_for_provider_ip',
                                provider_ip=provider_ip)


class HyperSwitchAgent(object):

    def __init__(self):
        super(HyperSwitchAgent, self).__init__()
        self.instance_id = cfg.CONF.host

        # the queue client for plug/unplug calls from nova driver
        endpoints = [self]
        target = messaging.Target(topic='hyperswitch-update',
                                  version='1.0',
                                  exchange='hyperswitch',
                                  server=cfg.CONF.host)
        self.server = rpc.get_server(target, endpoints)

        # the call back to nova driver init
        self.call_back = HyperSwitchAgentCallback()

        # instance according to configuration
        self.vif_driver = vif_hyperswitch_driver.HyperSwitchVIFDriver(
            instance_id=self.instance_id,
            call_back=self.call_back)

        self.vif_driver.startup_init()

        self.server.start()

    def daemon_loop(self):
        while True:
            eventlet.sleep(600)


def main():
    config.init(sys.argv[1:])

    agent = HyperSwitchAgent()
    # Start everything.
    LOG.info(_LI("Agent initialized successfully, now running. "))
    agent.daemon_loop()


if __name__ == "__main__":
    main()
