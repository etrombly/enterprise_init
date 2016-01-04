#!/usr/bin/env python3

import subprocess as sp
import os
import time
import shutil
from jinja2 import Template
import pexpect
import sys

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

print("Cloning template")
#sp.call([machinectl, "clone", "centos-template", hostname])
#workaround because machinectl clone is failing
sp.call(['systemd-nspawn', '-D', os.path.join('/var/lib/machines', hostname), '--template', '/var/lib/machines/centos-template', '/usr/bin/date'])

print("Configuring services")
shutil.copyfile("configs/nspawn.template", "/etc/systemd/nspawn/%s.nspawn" % (hostname))

with open("configs/host0.network.jinja", 'r') as template_file:
    template = Template(template_file.read())
    output = template.render(ip='192.168.0.9/24', gateway='192.168.0.1', dns='192.168.0.2', domain='etromb.local')
    
with open("/var/lib/machines/%s/etc/systemd/network/host0.network" % (hostname), 'w') as network:
    network.write(output)

with open("/var/lib/machines/%s/etc/hosts" % (hostname), 'a') as hosts:
    hosts.write("%s %s.%s %s" % (ip, hostname, domain, hostname))

with open("/var/lib/machines/%s/etc/hostname" % (hostname), 'w') as hosts:
    hosts.write("%s" % (hostname, ))

with open("/var/lib/machines/%s/etc/salt/minion_id" % (hostname), 'w') as minion:
    minion.write("%s" % (hostname, ))

print("Setting root password")
container = pexpect.spawn("systemd-nspawn -D %s" % os.path.join('/var/lib/machines', hostname))
container.expect('login:')
container.sendline('root')
container.expect('Password:')
container.sendline('root')
container.expect('UNIX password:')
container.sendline('root')
container.expect('new password:')
container.sendline(rpw)
container.expect('new password:')
container.sendline(rpw)
container.close()

print("Configuring salt")
sp.call([machinectl, 'start', hostname])
time.sleep(1)
#sp.call([machinectl, 'shell', 'salt', '/usr/bin/salt-key -y -a %s' % (hostname)])
container = pexpect.spawn([machinectl, 'login', hostname])
# '/usr/bin/salt-call state.highstate'
# ipa-client-install --domain=etromb.local --mkhomedir --enable-dns-updates --server=ipa.etromb.local -w 'test' --hostname=test.etromb.local -U -p admin