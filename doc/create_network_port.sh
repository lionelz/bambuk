

# create provider net/subnet
. openrc admin admin stack
neutron net-create --shared provider_net
neutron subnet-create --disable-dhcp --ip-version 4 provider_net 172.31.200.0/24

# create port
. openrc admin demo stack
neutron net-list
neutron port-create --device-id 123456 private
neutron port-list
neutron port-update 2866e543-b0a6-4ea4-9294-25200b48412f --binding:profile type=dict provider_mgnt_ip=172.31.200.25

neutron port-create --device-id 123456 --fixed-ip subnet_id=05ec0b25-851c-467c-aa42-b38006206993,ip_address=172.31.200.25 provider_net
neutron port-list
neutron port-update 247386c0-494b-4e27-85cf-2919767742a6 --binding:profile type=dict hyper_ip=10.0.0.4
