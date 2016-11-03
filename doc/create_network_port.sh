

# create provider net/subnet
. openrc admin admin stack
neutron net-create --shared provider_net
neutron subnet-create --disable-dhcp --ip-version 4 provider_net 172.31.200.0/24

# create port
. openrc admin demo stack
neutron net-list

neutron port-create --device-id 123456 --device-owner compute:nova private
neutron port-update 2866e543-b0a6-4ea4-9294-25200b48412f --binding:profile type=dict provider_mgnt_ip=172.31.200.197
neutron port-create --device-id 123456 --fixed-ip subnet_id=05ec0b25-851c-467c-aa42-b38006206993,ip_address=172.31.200.197 provider_net
neutron port-update 3cf91e9c-c722-45e5-a08e-7a9c4a2c7559 --binding:profile type=dict hyper_ip=10.0.0.4


neutron port-create --device-id 123457 --device-owner compute:nova private
neutron port-update 7d03186c-ba49-482e-a3f8-2482fb3c9e8f --binding:profile type=dict provider_mgnt_ip=172.31.200.21
neutron port-create --device-id 123457 --fixed-ip subnet_id=05ec0b25-851c-467c-aa42-b38006206993,ip_address=172.31.200.21 provider_net
neutron port-update c91fa694-55b3-42c6-9156-867d37f26ec1 --binding:profile type=dict hyper_ip=10.0.0.5


neutron port-create --device-id 123458 --device-owner compute:nova private
neutron port-update df8dbbd1-f589-4b66-8933-826229ae9c8e --binding:profile type=dict provider_mgnt_ip=172.31.200.217
neutron port-create --device-id 123458 --fixed-ip subnet_id=05ec0b25-851c-467c-aa42-b38006206993,ip_address=172.31.200.217 provider_net
neutron port-update 2ff60c3b-5af7-4b2d-a4e9-1593f069d67d --binding:profile type=dict hyper_ip=10.0.0.6


#Win user: Administrator/ZgGCA!G=af

neutron router-create router


neutron port-create --device-id 123460 --device-owner compute:nova private
neutron port-update 810618bd-6712-4d82-9482-848e3769deb1 --binding:profile type=dict provider_mgnt_ip=172.31.200.52
neutron port-create --device-id 123460 --fixed-ip subnet_id=05ec0b25-851c-467c-aa42-b38006206993,ip_address=172.31.200.52 provider_net
neutron port-update 59fd0b73-eb50-4462-96eb-c2f0955507b4 --binding:profile type=dict hyper_ip=10.0.0.9

