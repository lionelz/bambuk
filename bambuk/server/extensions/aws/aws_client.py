
from boto3.session import Session

class AWSClient(object):

    def __init__(self,
                 access_key_id,
                 secret_access_key,
                 region_name):
        self.session = Session(aws_access_key_id=access_key_id,
                               aws_secret_access_key=secret_access_key,
                               region_name=region_name)
        self._region_name = region_name
        self.ec2 = self.session.client('ec2')
        self.ec2_resource = self.session.resource('ec2')

    def find_vms(self, tag_name, tag_value):
        return self.ec2_resource.instances.filter(Filters=[{
            'Name': 'tag:%s' % tag_name,
            'Values': ['%s' % tag_value]}])

    def find_image_id(self, tag_name, tag_value):
        images = self.ec2_resource.images.filter(Filters=[{
            'Name': 'tag:%s' % tag_name,
            'Values': ['%s' % tag_value]}])
        for img in images:
            return img.id
        

    def create_instance(self,
                        user_data,
                        instance_type,
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
            InstanceType=instance_type,
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

# TODO: create ENI
    def create_port(self):
        pass
