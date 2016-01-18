#!/usr/bin/env python3

import subprocess as sp
import os
import time
import shutil
from jinja2 import Template
import pexpect
import sys
import Machinectl
import configparser

ctl = Machinectl.Machinectl()
prompt_string = "~\]#"
config = configparser.ConfigParser()
config.read('config.ini')

gateway=config['GLOBAL']['Gateway']
dns=config['IPA']['IP']
domain=config['GLOBAL']['Domain']
rpw =config['GLOBAL']['RootPW']
ipa_server = "%s.%s" % (config['IPA']['Hostname'], domain)

print("Provisioning new service")
role = input("Role?").upper()

if not config[role]:
    print("Role not in config.ini")
    sys.exit(1)

ip = config[role]['IP']
hostname = config[role]['Hostname']
fqdn = "%s.%s" % (hostname, domain)

print("Cloning template")
ctl.clone("centos-template", hostname)

print("Configuring services")
shutil.copyfile("configs/nspawn.template", "/etc/systemd/nspawn/%s.nspawn" % (hostname))

with open("configs/host0.network.jinja", 'r') as template_file:
    template = Template(template_file.read())
    output = template.render(ip=ip, gateway=gateway, dns=dns, domain=domain)
    
with open("/var/lib/machines/%s/etc/systemd/network/host0.network" % (hostname), 'w') as network:
    network.write(output)

with open("/var/lib/machines/%s/etc/hosts" % (hostname), 'a') as hosts:
    hosts.write("%s %s.%s %s" % (ip, hostname, domain, hostname))

with open("/var/lib/machines/%s/etc/hostname" % (hostname), 'w') as hosts:
    hosts.write("%s" % (hostname, ))

with open("/var/lib/machines/%s/etc/salt/minion_id" % (hostname), 'w') as minion:
    minion.write("%s" % (hostname, ))

print("Setting root password")
ctl.start(hostname)
time.sleep(1)
container = ctl.login(hostname)
container.expect('login:')
container.sendline('root')
container.expect('Password:')
container.sendline('root')
container.expect('password:')
container.sendline('root')
container.expect('password:')
container.sendline(rpw)
container.expect('password:')
container.sendline(rpw)

print("Configuring salt")
#check if salt is running, start if not
salt = ctl.login('salt')
salt.expect('login:')
salt.sendline('root')
salt.expect('Password:')
salt.sendline(rpw)
salt.expect(prompt_string)
salt.sendline('/usr/bin/salt-key -y -a %s' % (hostname))
salt.expect(prompt_string)
print(salt.before)
#time.sleep(1)
#container.sendline('salt-call state.highstate')
#container.expect(prompt_string)
#print(container.before)

print("Adding to domain")
container.sendline("ipa-client-install --domain=%s --mkhomedir --enable-dns-updates --server=%s -w '%s' --hostname=%s -U -p admin" % (domain, ipa_server, config['GLOBAL']['IPAPW'], fqdn))
container.expect(prompt_string)
print(container.before)