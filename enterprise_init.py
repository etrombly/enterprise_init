#!/usr/bin/env python3

import provision
import fetch

f = fetch.Fetch("centos-template")
f.fetch()

p = provision.Provision('IPA')
p.clone("centos-template")
p.configure()
p.ipaMaster()

p = provision.Provision('SALT')
p.clone("centos-template")
p.configure()
p.saltMaster()
p.ipaClient()

p = provision.Provision('IPA')
p.saltClient()

p = provision.Provision('TEST')
p.clone("centos-template")
p.configure()
p.ipaClient()
p.saltClient()