from neutronclient.common import extension


class Agentlessport(extension.NeutronClientExtension):
    resource = 'agentless_port'
    resource_plural = 'agentless_ports'
    path = 'agentless_ports'
    object_path = '/%s' % path
    resource_path = '/%s/%%s' % path
    versions = ['2.0']

