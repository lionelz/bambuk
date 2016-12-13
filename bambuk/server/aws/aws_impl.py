
from boto3 import session

from bambuk.server import config
from bambuk.server.extensions import hyperswitch


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
        image_id = self.find_image_id('hybrid_cloud_image', 'hyperswitch')

        net_interfaces = []
        i = 0
        for net in net_list:
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
            InstanceType=config.get_aws_flavor_map()[flavor],
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
