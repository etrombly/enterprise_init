#!/usr/bin/env python3
import urllib.request
import shutil
import tarfile
import os
import shutil
import pexpect

class Fetch(object):
    def __init__(self, name, cleanup = False):
        self.name = name
        self.dest = os.path.join('/var/lib/machines', name)
        self.cleanup = cleanup
        self.root_file = "rootfs.tar.xz"
        self.source =  "/tmp/" +  self.root_file
        if os.path.exists(self.dest):
            shutil.rmtree(self.dest)
        os.mkdir(self.dest)

    def fetch(self):
        try:
            self.download()
        except :
            pass
        self.extract()
        self.configure()

    def download(self):
        base_url =  "https://images.linuxcontainers.org"
        index_url =  base_url + "/meta/1.0/index-system"
        url = ""

        if os.path.exists(self.dest):
            print("Container already downloaded to %s" % (self.dest,))
            return

        print("Finding newest centos container")
        #read the index to find the current build
        with urllib.request.urlopen(index_url) as response:
            index =  response.read().decode("ascii")

        for line in index.split('\n'):
            if line.startswith("centos;7;amd64"):
                url = base_url + line.split(';')[5] + self.root_file

        if not url:
            raise urllib.error.URLError("Container not found")

        print("Found %s Downloading..." % (url, ))
        #download current build to /tmp
        with urllib.request.urlopen(url) as response, open(self.source, 'wb') as out_file:
            shutil.copyfileobj(response, out_file)

        print("Download finished")

    def extract(self):
        print("Extracting container")
        with tarfile.open(self.source, 'r:xz') as rootfs:
            rootfs.extractall(self.dest)
        if self.cleanup:
            print("Removing archive")
            os.remove(self.source)
        print("Extraction finished")

    def configure(self):
        prompt_string = "~\]#"
        print("Configuring container template")
        shutil.copyfile("configs/saltstack.repo",
                        os.path.join(self.dest, 'etc/yum.repos.d/saltstack.repo'))
        container = pexpect.spawn("systemd-nspawn -D %s" % self.dest)
        container.expect(prompt_string)
        container.sendline("rpm --import https://repo.saltstack.com/yum/redhat/7/x86_64/latest/SALTSTACK-GPG-KEY.pub")
        container.expect(prompt_string)
        container.sendline("yum clean expire-cache")
        container.expect(prompt_string)
        container.sendline("yum update")
        container.expect(prompt_string, timeout = 120)
        container.sendline("yum install -y salt-minion systemd-networkd systemd-resolved")
        container.expect(prompt_string, timeout = 600)
        container.sendline("systemctl enable salt-minion")
        container.expect(prompt_string)
        container.sendline("systemctl disable network")
        container.expect(prompt_string)
        container.sendline("systemctl enable systemd-networkd")
        container.expect(prompt_string)
        container.sendline("systemctl enable systemd-resolved")
        container.expect(prompt_string)
        os.remove(os.path.join(self.dest, "etc/resolv.conf"))
        os.remove(os.path.join(self.dest, "usr/lib/systemd/system/rhel-dmesg.service"))
        container.sendline("ln -s /run/systemd/resolve/resolv.conf /etc/resolv.conf")
        container.expect(prompt_string)
        container.close()
        print("Configuration finished")

if __name__ == "__main__":
    fetch = Fetch("centos-template") 
    fetch.fetch()