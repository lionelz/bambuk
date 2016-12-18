from neutronclient.common import extension
from bambuk._i18n import _


class Agentlessport(extension.NeutronClientExtension):
    resource = 'agentlessport'
    resource_plural = '%ss' % resource
    object_path = '/%s' % resource_plural
    resource_path = '/%s/%%s' % resource_plural
    versions = ['2.0']


class AgentlessportCreate(extension.ClientExtensionCreate, Agentlessport):
    """Create an agentless port information."""

    shell_command = 'agentlessport-create'

    def add_known_arguments(self, parser):
        parser.add_argument(
            'port_id', metavar='<NEUTRON_PORT_ID>',
            help=_('Neutron Port ID.'))
        parser.add_argument(
            'indice', metavar='<INDICE>',
            help=_('Indice of the port on the VM, begin from 0.'))
        parser.add_argument(
            '--flavor', dest='flavor',
            help=_('Network Flavor for the VM: 0G, 1G or 10G.'))
        parser.add_argument(
            '--vm-id', dest='vm_id',
            help=_('VM ID of the port.'))

    def args2body(self, parsed_args):
        body = {'agentlessport':
            {
                'port_id': parsed_args.port_id,
                'indice': parsed_args.indice,
            }
        }
        if parsed_args.flavor:
            body['agentlessport']['flavor'] = parsed_args.flavor
        if parsed_args.vm_id:
            body['agentlessport']['vm_id'] = parsed_args.vm_id
        if parsed_args.tenant_id:
            body['agentlessport']['tenant_id'] = parsed_args.tenant_id
        return body


class AgentlessportList(extension.ClientExtensionList, Agentlessport):
    """List agentless ports that belongs to a given tenant."""

    shell_command = 'agentlessport-list'
    list_columns = ['id', 'port_id', 'vm_id', 'tenant_id', 'indice']
    pagination_support = True
    sorting_support = True


class AgentlessportShow(extension.ClientExtensionShow, Agentlessport):
    """Show information of a given agentless port."""

    shell_command = 'agentlessport-show'


class AgentlessportDelete(extension.ClientExtensionDelete, Agentlessport):
    """Delete a given agentless port."""

    shell_command = 'agentlessport-delete'
