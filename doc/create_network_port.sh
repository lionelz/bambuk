

# create provider net/subnet
. openrc admin admin stack
neutron net-create --shared provider_net
neutron subnet-create --disable-dhcp --ip-version 4 provider_net 172.31.200.0/24

# create port
. openrc admin demo stack
neutron net-list
neutron port-create --device-id 123456 private
neutron port-list
neutron port-update 2866e543-b0a6-4ea4-9294-25200b48412f --binding:profile type=dict provider_mgnt_ip=172.31.200.197

neutron port-create --device-id 123456 --fixed-ip subnet_id=05ec0b25-851c-467c-aa42-b38006206993,ip_address=172.31.200.197 provider_net
neutron port-list
neutron port-update 3cf91e9c-c722-45e5-a08e-7a9c4a2c7559 --binding:profile type=dict hyper_ip=10.0.0.4
