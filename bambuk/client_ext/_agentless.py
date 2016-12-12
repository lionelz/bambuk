from neutronclient.common import extension


class Agentless(extension.NeutronClientExtension):
    resource = 'agentless'
    resource_plural = 'agentlesses'
    path = 'agentless'
    object_path = '/%s' % path
    resource_path = '/%s/%%s' % path
    versions = ['2.0']

