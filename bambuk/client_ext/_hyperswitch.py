from neutronclient.common import extension
from bambuk._i18n import _


class HyperSwitch(extension.NeutronClientExtension):
    resource = 'hyperswitch'
    resource_plural = '%ss' % resource
    object_path = '/%s' % resource_plural
    resource_path = '/%s/%%s' % resource_plural
    versions = ['2.0']


class HyperSwitchCreate(extension.ClientExtensionCreate, HyperSwitch):
    """Create hyperswitch information."""

    shell_command = 'hyperswitch-create'

    def add_known_arguments(self, parser):
        parser.add_argument(
            'flavor', metavar='<FLAVOR>',
            help=_('VM network flavor: 0G, 1G or 10G.'))

    def args2body(self, parsed_args):
        body = {'hyperswitch': {'flavor': parsed_args.flavor}, }
        return body


class HyperSwitchList(extension.ClientExtensionList, HyperSwitch):
    """List hyperswitch that belongs to a given tenant."""

    shell_command = 'hyperswitch-list'
    list_columns = ['id', 'device_id', 'tenant_id', 'flavor']
    pagination_support = True
    sorting_support = True


class HyperSwitchShow(extension.ClientExtensionShow, HyperSwitch):
    """Show information of a given hyperswitch."""

    shell_command = 'hyperswitch-show'


class HyperSwitchDelete(extension.ClientExtensionDelete, HyperSwitch):
    """Delete a given hyperswitch."""

    shell_command = 'hyperswitch-delete'
