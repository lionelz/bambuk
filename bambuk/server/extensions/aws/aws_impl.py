

from server.extensions import hyperswitch

from oslo_config import cfg
from bambuk.server.extensions import aws


class AWSProvider(hyperswitch.ProviderDriver):
    
    def __init__(self):
        self.aws_client = aws.aws_client(
            cfg.CONF.hyperswitch.aws_access_key_id,
            cfg.CONF.hyperswitch.aws_secret_access_key,
            cfg.CONF.hyperswitch.aws_region_name)

    def create_port(self):
        pass

    def search_port(self, provider_ip):
        pass

    def launch_vm(self, image_id, flavor):
        pass
