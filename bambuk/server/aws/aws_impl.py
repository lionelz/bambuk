
from boto3 import session

from bambuk.server import config
from bambuk.server import provider_api

from oslo_log import log as logging


LOG = logging.getLogger(__name__)


MAX_NIC = {
    'c1.medium': 2,
    'c1.xlarge': 4,
    'c3.large': 3,
    'c3.xlarge': 4,
    'c3.2xlarge': 4,
    'c3.4xlarge': 8,
    'c3.8xlarge': 8,
    'c4.large': 3,
    'c4.xlarge': 4,
    'c4.2xlarge': 4,
    'c4.4xlarge': 8,
    'c4.8xlarge': 8,
    'cc2.8xlarge': 8,
    'cg1.4xlarge': 8,
    'cr1.8xlarge': 8,
    'd2.xlarge': 4,
    'd2.2xlarge': 4,
    'd2.4xlarge': 8,
    'd2.8xlarge': 8,
    'g2.2xlarge': 4,
    'g2.8xlarge': 8,
    'hi1.4xlarge': 8,
    'hs1.8xlarge': 8,
    'i2.xlarge': 4,
    'i2.2xlarge': 4,
    'i2.4xlarge': 8,
    'i2.8xlarge': 8,
    'm1.small': 2,
    'm1.medium': 2,
    'm1.large': 3,
    'm1.xlarge': 4,
    'm2.xlarge': 4,
    'm2.2xlarge': 4,
    'm2.4xlarge': 8,
    'm3.medium': 2,
    'm3.large': 3,
    'm3.xlarge': 4,
    'm3.2xlarge': 4,
    'm4.large': 2,
    'm4.xlarge': 4,
    'm4.2xlarge': 4,
    'm4.4xlarge': 8,
    'm4.10xlarge': 8,
    'm4.16xlarge': 8,
    'p2.xlarge': 4,
    'p2.8xlarge': 8,
    'p2.16xlarge': 8,
    'r3.large': 3,
    'r3.xlarge': 4,
    'r3.2xlarge': 4,
    'r3.4xlarge': 8,
    'r3.8xlarge': 8,
    'r4.large': 3,
    'r4.xlarge': 4,
    'r4.2xlarge': 4,
    'r4.4xlarge': 8,
    'r4.8xlarge': 8,
    'r4.16xlarge': 15,
    't1.micro': 2,
    't2.nano': 2,
    't2.micro': 2,
    't2.small': 2,
    't2.medium': 3,
    't2.large': 3,
    't2.xlarge': 3,
    't2.2xlarge': 3,
    'x1.16xlarge': 8,
    'x1.32xlarge': 8,
}


class AWSProvider(provider_api.ProviderDriver):
    
    def __init__(self):
        self._access_key_id = config.get_aws_access_key_id()
        self._secret_access_key = config.get_aws_secret_access_key()
        self._region_name = config.get_aws_region_name()
        self.session = session.Session(
            aws_access_key_id=self._access_key_id,
            aws_secret_access_key=self._secret_access_key,
            region_name=self._region_name)
        self.ec2 = self.session.client('ec2')
        self.ec2_resource = self.session.resource('ec2')

    def _find_subnets(self, vpc, tag_name, tag_value):
        return vpc.subnets.filter(Filters=[{
            'Name': 'tag:%s' % tag_name,
            'Values': ['%s' % tag_value]}])

    def _find_vms(self, tag_name, tag_values):
        return self.ec2_resource.instances.filter(Filters=[{
            'Name': 'tag:%s' % tag_name,
            'Values': tag_values}])

    def _find_image_id(self, tag_name, tag_value):
        images = self.ec2_resource.images.filter(Filters=[{
            'Name': 'tag:%s' % tag_name,
            'Values': ['%s' % tag_value]}])
        for img in images:
            return img.id

    def get_vms_subnet(self):
        vpc = self.ec2_resource.Vpc(config.get_aws_vpc())
        subnets_id = []
        tag_name = 'Name'
        for cidr in config.get_vms_cidr():
            tag_val = 'vms_%s' % cidr
            subnets = self._find_subnets(vpc, tag_name, tag_val)
            subnet_id = None
            for subnet in subnets:
                subnet_id = subnet.id
            if not subnet_id:
                subnet = self.ec2.create_subnet(
                    VpcId=config.get_aws_vpc(),
                    CidrBlock=cidr
                )
                subnet_id = subnet['Subnet']['SubnetId']
                self.ec2.create_tags(
                    Resources=[subnet_id],
                    Tags=[{
                        'Key': tag_name,
                        'Value': tag_val
                    }]
                )
            subnets_id.append(subnet_id)
        return subnets_id

    def get_hyperswitch_host_name(self,
                                  hybrid_cloud_vm_id=None,
                                  hybrid_cloud_tenant_id=None):
        if hybrid_cloud_vm_id:
            vms = self._find_vms(
                'hybrid_cloud_vm_id',
                [hybrid_cloud_vm_id])
            size = sum(1 for _ in vms)
            host = 'vm-%s-%d' % (hybrid_cloud_vm_id, size)
        else:
            vms = self._find_vms(
                'hybrid_cloud_tenant_id',
                [hybrid_cloud_tenant_id])
            size = sum(1 for _ in vms)
            host = 'tenant-%s-%d' % (hybrid_cloud_tenant_id, size)
        return host

    def _aws_instance_to_dict(self, aws_instance):
        host = None
        vm_id = None
        tenant_id = None
        for tag in aws_instance.tags:
            if tag['Key'] == 'Name':
                host = tag['Value']
            if tag['Key'] == 'hybrid_cloud_vm_id':
                vm_id = tag['Value']
            if tag['Key'] == 'hybrid_cloud_tenant_id':
                tenant_id = tag['Value']
        res = {
            'id': host,
            'vm_id': vm_id,
            'tenant_id': tenant_id,
            'instance_id': aws_instance.id,
            'instance_type': aws_instance.instance_type,
            'private_ip':  aws_instance.private_ip_address,
        }
        i = 0
        for net_int in aws_instance.network_interfaces_attribute:
            if i == 0:
                res['mgnt_ip'] = net_int['PrivateIpAddress']
            if i == 1:
                res['data_ip'] = net_int['PrivateIpAddress']
            if i > 1:
                res['vms_ip_%s' % (i - 2)] = net_int['PrivateIpAddress']
            i = i + 1
        return res

    def launch_hyperswitch(self,
                           user_data,
                           flavor,
                           net_list,
                           hybrid_cloud_vm_id=None,
                           hybrid_cloud_tenant_id=None):
        # find the image according to a tag hybrid_cloud_image=hyperswitch
        image_id = self._find_image_id('hybrid_cloud_image', 'hyperswitch')
        instance_type = config.get_aws_hs_flavor_map()[flavor]
        net_interfaces = []
        i = 0
        for net in net_list:
            if i < MAX_NIC[instance_type]:
                net_interfaces.append(
                    {
                        'DeviceIndex': i,
                        'SubnetId': net['name'],
                        'Groups': [net['security_group']],
                    }
                )
                i = i + 1 
        user_metadata = ''
        for k, v in user_data.iteritems():
            user_metadata = '%s\n%s=%s' % (user_metadata, k, v)
        # create the instance
        aws_instance = self.ec2_resource.create_instances(
            ImageId=image_id,
            MinCount=1,
            MaxCount=1,
            UserData=user_metadata,
            InstanceType=instance_type,
            InstanceInitiatedShutdownBehavior='stop',
            NetworkInterfaces=net_interfaces,
        )[0]

        host = self.get_hyperswitch_host_name(
            hybrid_cloud_vm_id,
            hybrid_cloud_tenant_id)
        tags = [{'Key': 'hybrid_cloud_tenant_id',
                 'Value': hybrid_cloud_tenant_id},
                {'Key': 'hybrid_cloud_type',
                 'Value': 'hyperswitch'},
                {'Key': 'Name',
                 'Value': host}]
        if hybrid_cloud_vm_id:
            tags.append({'Key': 'hybrid_cloud_vm_id',
                         'Value': hybrid_cloud_vm_id})
        self.ec2.create_tags(Resources=[aws_instance.id],
                             Tags=tags)

        aws_instance.wait_until_running()
        aws_instance.reload()
        return self._aws_instance_to_dict(aws_instance)

    def _add_vms_from_tags(self, tag, values, res):
        if values:
            aws_instances = self._find_vms(
                tag, values)
            for aws_instance in aws_instances:
                res.append(self._aws_instance_to_dict(aws_instance))

    def get_hyperswitchs(self,
                         names=None,
                         hyperswitch_ids=None,
                         vm_ids=None,
                         tenant_ids=None):
        LOG.debug('get hyperswitch for (%s, %s, %s, %s).' % (
            names, hyperswitch_ids, vm_ids, tenant_ids))
        res = []
        self._add_vms_from_tags('Name', names, res)
        self._add_vms_from_tags('Name', hyperswitch_ids, res)
        self._add_vms_from_tags('hybrid_cloud_vm_id', vm_ids, res)
        self._add_vms_from_tags('hybrid_cloud_tenant_id', tenant_ids, res)

        if not names and not hyperswitch_ids and not vm_ids and not tenant_ids:
            self._add_vms_from_tags('hybrid_cloud_type', ['hyperswitch'], res)

        LOG.debug('found hyperswitchs for (%s, %s, %s) = %s.' % (
            hyperswitch_ids, vm_ids, tenant_ids, res))
        return res

    def delete_hyperswitch(self, hyperswitch_id):
        LOG.debug('hyperswitch to delete: %s.' % (hyperswitch_id))
        aws_instances = self._find_vms(
            'Name',
            [hyperswitch_id])
        LOG.debug('aws_instances to delete: %s.' % (aws_instances))
        for aws_instance in aws_instances:
            aws_instance.stop()
            aws_instance.wait_until_stopped()
            aws_instance.terminate()
            aws_instance.wait_until_terminated()

    def _network_interface_dict(self, net_int):
        LOG.debug('aws net interface: %s.' % net_int)
        port_id = None
        vm_id = None
        tenant_id = None
        indice = None
        for tag in net_int['TagSet']:
            if tag['Key'] == 'hybrid_cloud_port_id':
                port_id = tag['Value']
            if tag['Key'] == 'hybrid_cloud_vm_id':
                vm_id = tag['Value']
            if tag['Key'] == 'hybrid_cloud_tenant_id':
                tenant_id = tag['Value']
            if tag['Key'] == 'hybrid_cloud_indice':
                tenant_id = tag['Value']
        res = {
            'ip': net_int['PrivateIpAddress'],
            'port_id': port_id,
            'vm_id': vm_id,
            'tenant_id': tenant_id,
            'indice': indice
        }
        LOG.debug('net interface: %s.' % res)
        return res

    def _add_network_interfaces_from_filter(self, tag, values, res):
        if values:
            net_ints = self.ec2.describe_network_interfaces(
                Filters=[{
                    'Name': tag,
                    'Values': values}]
            )
            for net_int in net_ints:
                res.append(self._network_interface_dict(net_int))

    def create_network_interface(
            self,
            port_id,
            vm_id,
            tenant_id,
            indice,
            subnet,
            security_group):
        LOG.debug('create net interface (%s, %s, %s, %d, %s, %s).' % (
            port_id, vm_id, tenant_id, indice, subnet, security_group))
        net_int = self.ec2.create_network_interface(
            SubnetId=subnet,
            Groups=[security_group]
        )
        LOG.debug('aws net interface: %s.' % (net_int))
        int_id = net_int['NetworkInterface']['NetworkInterfaceId']
        tags = [{'Key': 'hybrid_cloud_port_id',
                 'Value': port_id},
                  {'Key': 'hybrid_cloud_tenant_id',
                 'Value': tenant_id},
                  {'Key': 'hybrid_cloud_indice',
                 'Value': str(indice)}]
        if vm_id:
            tags.append({'Key': 'hybrid_cloud_vm_id',
                         'Value': vm_id})
        self.ec2.create_tags(
            Resources=[int_id],
            Tags=tags)
        net_ints = self.ec2.describe_network_interfaces(
            NetworkInterfaceIds=[int_id])
        for net_int in net_ints['NetworkInterfaces']:
            return self._network_interface_dict(net_int)

    def delete_network_interface(
            self, port_id):
        net_ints = self.get_network_interfaces(self, port_id)
        for net_int in net_ints:
            self.ec2.delete_network_interface(
                net_int['NetworkInterface']['NetworkInterfaceId'])

    def get_network_interfaces(self,
                               name,
                               port_ids=None,
                               vm_ids=None,
                               private_ips=None,
                               tenant_ids=None,
                               indices=None):
        res = []
        self._add_network_interfaces_from_filter(
            'tag:hybrid_cloud_port_id', [name], res)
        self._add_network_interfaces_from_filter(
            'tag:hybrid_cloud_port_id', port_ids, res)
        self._add_network_interfaces_from_filter(
            'tag:hybrid_cloud_vm_id', vm_ids, res)
        self._add_network_interfaces_from_filter(
            'addresses.private-ip-address', private_ips, res)
        self._add_network_interfaces_from_filter(
            'tag:hybrid_cloud_tenant_id', tenant_ids, res)
        self._add_network_interfaces_from_filter(
            'tag:hybrid_cloud_indice', indices, res)

        return res
