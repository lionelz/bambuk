

# create fake provider tenant, net and subnet
export OS_USERNAME=admin
export OS_PASSWORD=stack
export OS_TENANT_NAME=admin
export OS_PROJECT_NAME=admin
keystone tenant-create  --name fake-provider-tenant --enabled true
keystone user-create --name fake --tenant fake-provider-tenant --enabled true --pass fake

export OS_USERNAME=fake
export OS_PASSWORD=fake
export OS_TENANT_NAME=fake-provider-tenant
export OS_PROJECT_NAME=fake-provider-tenant
neutron net-create provider_net
neutron subnet-create --disable-dhcp --ip-version 4 provider_net 172.31.200.0/24

# create neutron port
export OS_USERNAME=demo
export OS_PASSWORD=stack
export OS_TENANT_NAME=demo
export OS_PROJECT_NAME=demo
neutron net-list
neutron port-list
neutron port-create --device-id 123456 --device-owner compute:nova private
neutron port-create --device-id 123500 --device-owner compute:nova private2

# create fake neutron port
export OS_USERNAME=fake
export OS_PASSWORD=fake
export OS_TENANT_NAME=fake-provider-tenant
export OS_PROJECT_NAME=fake-provider-tenant
neutron port-create --device-id 123456 --fixed-ip subnet_id=e03c09af-3217-49e5-9439-ccadabfaa428,ip_address=172.31.200.55 --name f3b2a8d2-75cf-441c-a358-83cbfaa1c82d provider_net
neutron port-create --device-id 123500 --fixed-ip subnet_id=e03c09af-3217-49e5-9439-ccadabfaa428,ip_address=172.31.200.53 --name 218c7485-e96c-4d84-9d2f-4d719763f96d provider_net


#Win user: Administrator/ZgGCA!G=af
neutron router-create router


