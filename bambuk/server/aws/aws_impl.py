
from boto3 import session

from bambuk.server import config
from bambuk.server.extensions import hyperswitch


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


class AWSProvider(hyperswitch.ProviderDriver):
    
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
        return self.ec2_resource.instances.filter(Filters=[{
            'Name': 'tag:%s' % tag_name,
            'Values': ['%s' % tag_value]}])

    def _find_vms(self, tag_name, tag_value):
        return self.ec2_resource.instances.filter(Filters=[{
            'Name': 'tag:%s' % tag_name,
            'Values': ['%s' % tag_value]}])

    def _find_image_id(self, tag_name, tag_value):
        images = self.ec2_resource.images.filter(Filters=[{
            'Name': 'tag:%s' % tag_name,
            'Values': ['%s' % tag_value]}])
        for img in images:
            return img.id

    def get_vms_subnet(self):
        vpc = self.ec2_resource.Vpc(config.get_aws_vpc())
        subnets_id = []
        for cidr in config.get_vms_cidr():
            subnets = self.check_vms_subnet(
                vpc,
                'agentless_vms_cidr',
                '%s' % cidr
            )
            subnet_id = None
            for subnet in subnets:
                subnet_id = subnet.id
            if not subnet_id:
                subnet_id = self.ec2.create_subnet(
                    VpcId=config.get_aws_vpc(),
                    CidrBlock=cidr
                ).id
            subnets_id.append(subnet_id)
        return subnets_id

    def get_hyperswitch_host_name(self,
                                  hybrid_cloud_vm_id=None,
                                  hybrid_cloud_tenant_id=None):
        if hybrid_cloud_vm_id:
            vms = self._find_vms(
                'hybrid_cloud_vm_id',
                hybrid_cloud_vm_id)
            size = sum(1 for _ in vms)
            host = 'vm-%s-%d' % (hybrid_cloud_vm_id, size)
        else:
            vms = self._find_vms(
                'hybrid_cloud_tenant_id',
                hybrid_cloud_tenant_id)
            size = sum(1 for _ in vms)
            host = 'tenant-%s-%d' % (hybrid_cloud_tenant_id, size)
        return host
        

    def launch_hyperswitch(self,
                           user_data,
                           flavor,
                           net_list,
                           hybrid_cloud_vm_id=None,
                           hybrid_cloud_tenant_id=None):
        # find the image according to a tag hybrid_cloud_image=hyperswitch
        image_id = self._find_image_id('hybrid_cloud_image', 'hyperswitch')
        image_type = config.get_aws_flavor_map()[flavor]
        net_interfaces = []
        i = 0
        for net in net_list:
            if i < MAX_NIC[image_type]:
                net_interfaces.append(
                    {
                        'DeviceIndex': i,
                        'SubnetId': net['name'],
                        'Groups': [net['security_group']],
                    }
                )
                i = i + 1 
        # create the instance
        aws_instance = self.ec2_resource.create_instances(
            ImageId=image_id,
            MinCount=1,
            MaxCount=1,
            UserData=user_data,
            InstanceType=image_type,
            InstanceInitiatedShutdownBehavior='stop',
            NetworkInterfaces=net_interfaces,
        )[0]
        aws_instance.wait_until_running()

        instance_id = aws_instance.id

        if hybrid_cloud_vm_id:
            self.ec2.create_tags(Resources=[instance_id],
                                 Tags=[{'Key': 'hybrid_cloud_vm_id',
                                        'Value': hybrid_cloud_vm_id}])
        if hybrid_cloud_tenant_id:
            self.ec2.create_tags(Resources=[instance_id],
                                 Tags=[{'Key': 'hybrid_cloud_tenant_id',
                                        'Value': hybrid_cloud_tenant_id}])
