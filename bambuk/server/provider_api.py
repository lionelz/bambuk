import abc


class ProviderDriver(object):

    @abc.abstractmethod
    def get_vms_subnet(self):
        return []

    @abc.abstractmethod
    def get_hyperswitch_host_name(self,
                                  hybrid_cloud_vm_id=None,
                                  hybrid_cloud_tenant_id=None):
        pass

    @abc.abstractmethod
    def launch_hyperswitch(self,
                           user_data,
                           flavor,
                           net_list,
                           hybrid_cloud_vm_id=None,
                           hybrid_cloud_tenant_id=None):
        pass

    @abc.abstractmethod
    def get_hyperswitchs(self,
                         names=None,
                         hyperswitch_ids=None,
                         vm_ids=None,
                         tenant_ids=None):
        return []

    @abc.abstractmethod
    def delete_hyperswitch(self, hyperswitch_id):
        pass
