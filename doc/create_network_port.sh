

# create provider net/subnet
. openrc admin admin stack
neutron net-create --shared provider_net
neutron subnet-create --disable-dhcp --ip-version 4 provider_net 172.31.200.0/24

# create port
. openrc admin demo stack
neutron net-list

neutron port-create --device-id 123456 --device-owner compute:nova private
neutron port-create --device-id 123456 --fixed-ip subnet_id=05ec0b25-851c-467c-aa42-b38006206993,ip_address=172.31.200.197 --name 3cf91e9c-c722-45e5-a08e-7a9c4a2c7559 provider_net


#Win user: Administrator/ZgGCA!G=af

neutron router-create router

neutron port-create --device-id 123500 --device-owner compute:nova private2
neutron port-update 218c7485-e96c-4d84-9d2f-4d719763f96d --binding:profile type=dict provider_mgnt_ip=172.31.200.53
neutron port-create --device-id 123500 --fixed-ip subnet_id=05ec0b25-851c-467c-aa42-b38006206993,ip_address=172.31.200.53 provider_net
neutron port-update fd42a4fb-7e22-44a8-9861-37503dd4059c --binding:profile type=dict hyper_ip=10.0.1.4

