#!/usr/bin/env python3

import time
import shutil
from jinja2 import Template
import sys
import Machinectl
import yaml
import os

class Provision(object):
    def __init__(self, role):
        self.ctl = Machinectl.Machinectl()
        self.prompt_string = "~\]#"
        with open('config.yaml') as config_file:
            self.config = yaml.safe_load(config_file)

        self.gateway = self.config['Globals']['Gateway']
        self.dns = self.config['Roles']['IPA']['IP']
        self.domain = self.config['Globals']['Domain']
        self.realm = self.config['Globals']['Realm']
        self.rpw  = self.config['Globals']['RootPW']
        self.ipapw = self.config['Globals']['IPAPW']
        self.ipa_server = "%s.%s" % (self.config['Roles']['IPA']['Hostname'], self.domain)
        self.role = role

        if not self.config['Roles'][role]:
            print("Role not in config.ini")
            sys.exit(1)

        self.ip = self.config['Roles'][self.role]['IP']
        self.hostname = self.config['Roles'][self.role]['Hostname']
        self.fqdn = "%s.%s" % (self.hostname, self.domain)

    def clone(self, template):
        self.ctl.clone(template, self.hostname)

    def login(self):
        return self.ctl.login(self.hostname, 'root', self.rpw)

    def configure(self):
        if not os.path.exists("/etc/systemd/nspawn"):
            os.mkdir("/etc/systemd/nspawn")

        if "ipa" in self.hostname:
            shutil.copyfile("configs/ipa.nspawn.template", "/etc/systemd/nspawn/ipa.nspawn")
        else:
            shutil.copyfile("configs/nspawn.template", "/etc/systemd/nspawn/%s.nspawn" % (self.hostname))

        with open("configs/host0.network.jinja", 'r') as template_file:
            template = Template(template_file.read())
            output = template.render(ip = self.ip, gateway = self.gateway,
                                     dns = self.dns, domain = self.domain)

        with open("/var/lib/machines/%s/etc/systemd/network/host0.network" % self.hostname, 'w') as network:
            network.write(output)

        with open("/var/lib/machines/%s/etc/hosts" % self.hostname, 'a') as hosts:
            hosts.write("%s %s.%s %s" % (self.ip, self.hostname, self.domain, self.hostname))

        with open("/var/lib/machines/%s/etc/hostname" % self.hostname, 'w') as hosts:
            hosts.write("%s" % self.hostname)

        with open("/var/lib/machines/%s/etc/salt/minion_id" % self.hostname, 'w') as minion:
            minion.write("%s" % self.hostname)

        self.ctl.start(self.hostname)
        while b'dbus' not in self.ctl.status(self.hostname):
            print(self.ctl.status(self.hostname))
            time.sleep(.5)
        container = self.ctl.login(self.hostname)
        container.expect('login:')
        container.sendline('root')
        container.expect('Password:')
        container.sendline('root')
        container.expect('password:')
        container.sendline('root')
        container.expect('password:')
        container.sendline(self.rpw)
        container.expect('password:')
        container.sendline(self.rpw)
        container.expect(self.prompt_string)
        container.close()

    def saltClient(self):
        #TODO check if salt is running, start if not
        salt = self.ctl.login('salt', 'root', self.rpw)
        salt.sendline('/usr/bin/salt-key -y -a %s' % self.hostname)
        salt.expect(self.prompt_string)
        salt.close()

    def saltMaster(self):
        os.rmdir('/var/lib/machines/%s/srv' % self.hostname)
        shutil.copytree('configs/srv', '/var/lib/machines/%s/srv' % self.hostname)
        container = self.ctl.login(self.hostname, 'root', self.rpw)
        container.sendline("yum install -y salt-master")
        container.expect(self.prompt_string, timeout = 600)
        container.sendline("systemctl enable salt-master --now")
        container.expect(self.prompt_string)
        container.close()

    def ipaClient(self):
        container = self.ctl.login(self.hostname, 'root', self.rpw)
        container.sendline("ipa-client-install --domain=%s --mkhomedir --enable-dns-updates --server=%s -w '%s' --hostname=%s -U -p admin" %
                           (self.domain, self.ipa_server, self.ipapw, self.fqdn))
        container.expect(self.prompt_string, timeout=90)
        container.close()

    def ipaMaster(self):
        container = self.ctl.login(self.hostname, 'root', self.rpw)
        container.sendline("echo nameserver %s > /etc/resolv.conf" % self.config['Roles']['IPA']['DNS'])
        container.expect(self.prompt_string)
        container.sendline("yum install -y ipa-server ipa-server-dns")
        container.expect(self.prompt_string, timeout = 600)
        container.sendline("ipa-server-install -n %s -r %s -p '%s' -a '%s' --hostname=%s --setup-dns --forwarder=%s -U" %
                           (self.domain, self.realm, self.ipapw, self.ipapw, self.fqdn, self.config['Roles']['IPA']['DNS']))
        container.expect(self.prompt_string, timeout = 1200)
        container.sendline("authconfig --enablemkhomedir --update")
        container.expect(self.prompt_string)
        container.close()