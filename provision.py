#!/usr/bin/env python3

import subprocess as sp
import sys
import os
import stat
import time
import shutil
from jinja2 import Template

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
sp.call([machinectl, "clone", "centos-template", hostname])
shutil.copyfile("configs/nspawn.template", "/etc/systemd/nspawn/%s.nspawn" % (hostname))

with open("configs/host0.network.jinja", 'r') as template_file:
    template = Template(template_file.read())
    output = template.render(ip='test', gateway='test', dns='test', domain='test')
    
with open("/var/lib/machines/%s/etc/systemd/network/host0.network" % (hostname), 'w') as network:
    network.write(output)

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