#!/usr/bin/env python3

import subprocess as sp
import sys
import os
import stat
import time

machinectl = "/usr/bin/machinectl"

print("Provisioning new service")
hostname = input("Hostname?")
domain = input("Domain name?")
ip = input("IP?")
rpw = input("Root password?")
answer = input("Proceed with %s, %s, %s, %s?" % (hostname, domain, ip, rpw))

if not "y" in answer.lower():
    print("exiting")
    sys.exit()

print("Bootstrapping service")
with open("/etc/systemd/nspawn/%s.nspawn" % (hostname), 'w') as nspawn_file:
    nspawn_file.write("[Exec]\nBoot=True\n\n[Network]\nBridge=br0")

sp.call([machinectl, "clone", "arch", hostname])

with open("/var/lib/machines/%s/etc/systemd/network/host0.network" % (hostname), 'w') as network:
    lines = ["[Match]\nName=host0\n[Network]"]
    lines.append("Address=%s/24" % (ip, ))
    lines.append("Gateway=192.168.0.1")
    lines.append("DNS=192.168.0.2")
    lines.append("Domains=%s" % (domain, ))
    network.write("\n".join(lines))

with open("/var/lib/machines/%s/etc/hosts" % (hostname), 'a') as hosts:
    hosts.write("%s %s.%s %s" % (ip, hostname, domain, hostname))

with open("/var/lib/machines/%s/etc/hostname" % (hostname), 'a') as hosts:
    hosts.write("%s" % (hostname, ))
    
with open("/var/lib/machines/%s/firstboot.sh" % (hostname), 'w') as script:
    lines = ["#!/bin/bash"]
    lines.append("echo 'root:%s' | chpasswd" % (rpw, ))
    lines.append("ln -sf /dev/null /etc/systemd/network/80-container-host0.network")
    lines.append("systemctl enable systemd-networkd")
    lines.append("systemctl enable systemd-resolved")
    lines.append("rm /etc/resolv.conf")
    lines.append("ln -s /run/systemd/resolve/resolv.conf /etc/resolv.conf")
    lines.append("systemctl enable salt-minion")
    lines.append("systemctl enable sssd")
    lines.append("mkdir /etc/salt")
    lines.append("echo %s > /etc/salt/minion_id" % hostname)
    script.write("\n".join(lines))

os.chmod("/var/lib/machines/%s/firstboot.sh" % (hostname), stat.S_IRWXU)
sp.call([machinectl, 'start', hostname])
time.sleep(2)
sp.call([machinectl, 'shell', hostname, '/firstboot.sh'])
sp.call([machinectl, 'reboot', hostname])
time.sleep(1)
sp.call([machinectl, 'start', hostname])
time.sleep(1)
sp.call([machinectl, 'shell', 'salt', '/usr/bin/salt-key -y -a %s' % (hostname)])
sp.call([machinectl, 'shell', hostname, '/usr/bin/salt-call state.highstate'])