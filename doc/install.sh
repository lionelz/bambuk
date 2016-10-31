#!/bin/bash
set -x

# based on ubuntu 14.04.03
# set 3 manual network interfaces
# manual sysctl configuration
# set in /etc/sysctl.conf
# edit_sysctl net.ipv4.conf.all.rp_filter 0
# edit_sysctl net.ipv4.conf.default.rp_filter 0
# sysctl -p

# install the nova/neutron packages
add-apt-repository -y cloud-archive:mitaka
apt-get -y update
apt-get -y dist-upgrade
apt-get --no-install-recommends -y install neutron-plugin-openvswitch-agent neutron-l3-agent
apt-get -y install bridge-utils openvpn easy-rsa python-ryu

ovs-vsctl --may-exist add-br br-ex

#remove automatic openvpn start
update-rc.d openvpn disable

FROM_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )/.."

# hyper agent python packages
python ./setup.py install

# binaries
bin_files='hyperswitch-config'
for f in $bin_files
do
    rm -f /usr/bin/$f
    cp $FROM_DIR/bin/$f /usr/bin
done

# init conf
rm -f /etc/init/hyperswitch*
cp -r $FROM_DIR/etc/init/* /etc/init

# etc hyperswitch conf
rm -rf /etc/hyperswitch
cp -r $FROM_DIR/etc/hyperswitch /etc

# neutron template
rm -rf `find /etc/neutron -name "*.tmpl"`
cp $FROM_DIR/etc/neutron/neutron.conf.tmpl /etc/neutron
cp $FROM_DIR/etc/neutron/plugins/ml2/openvswitch_agent.ini.tmpl /etc/neutron/plugins/ml2

# var folder
rm -rf /var/log/hyperswitch
mkdir /var/log/hyperswitch
