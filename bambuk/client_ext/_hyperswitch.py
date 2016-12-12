from neutronclient.common import extension
from neutronclient.common import utils


class HyperSwitch(extension.NeutronClientExtension):
    resource = 'hyperswitch'
    resource_plural = 'hyperswitchs'
    path = 'hyperswitch'
    object_path = '/%s' % path
    resource_path = '/%s/%%s' % path
    versions = ['2.0']


class HyperSwitchCreate(extension.ClientExtensionCreate, HyperSwitch):
    """Create hyperswitch information."""

    shell_command = 'hyperswitch-create'

    def add_known_arguments(self, parser):
        parser.add_argument(
            'flavor', metavar='<FLAVOR>',
            help=_('VM network flavor: 0G, 1G or 10G.'))
        parser.add_argument(
            'vm_id', metavar='<VM_ID>',
            help=_('VM ID if created for one VM.'))
        parser.add_argument(
            'tenant_id', metavar='<TENANT_ID>',
            help=_('TENANT ID if created for a tenant.'))

    def args2body(self, parsed_args):
        body = {'hyperswitch': {'flavor': parsed_args.flavor}, }
        if parsed_args.tenant_id:
            body['hyperswitch']['tenant_id'] = parsed_args.tenant_id
        if parsed_args.vm_id:
            body['hyperswitch']['vm_id'] = parsed_args.vm_id
        return body


class HyperSwitchList(extension.ClientExtensionList, HyperSwitch):
    """List hyperswitch that belongs to a given tenant."""

    shell_command = 'hyperswitch-list'
    list_columns = ['vm_id', 'tenant_id']
    pagination_support = True
    sorting_support = True


class HyperSwitchShow(extension.ClientExtensionShow, HyperSwitch):
    """Show information of a given hyperswitch."""

    shell_command = 'hyperswitch-show'


class HyperSwitchDelete(extension.ClientExtensionDelete, HyperSwitch):
    """Delete a given hyperswitch."""

    shell_command = 'hyperswitch-delete'
