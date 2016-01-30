#!/usr/bin/env python3

import provision
import fetch
import time

#f = fetch.Fetch("centos-template")
#f.fetch()

ipa = provision.Provision('IPA')
ipa.clone("centos-template")
ipa.configure()
ipa.ipaMaster()

salt = provision.Provision('SALT')
salt.clone("centos-template")
salt.configure()
salt.saltMaster()
salt.ipaClient()
salt.saltClient()

ipa.saltClient()

p = provision.Provision('SQUID')
p.clone("centos-template")
p.configure()
p.ipaClient()
p.saltClient()

time.sleep(2)
container = salt.login()
container.sendline("salt '%s' state.apply squid" % p.hostname)
container.expect('~\]#', timeout = 600)