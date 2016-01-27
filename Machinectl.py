#!/usr/bin/env python3

import pexpect
import sys

class Machinectl(object):
    def __init__(self):
        self.prompt_string = "~\]#"

    def start(self, name):
        pexpect.run('machinectl start %s' % name)

    def login(self, name, user = None, pw = None):
        shell = pexpect.spawnu('machinectl login %s' % name, logfile = sys.stdout)
        if (user is not None) and (pw is not None):
            shell.expect('login:')
            shell.sendline(user)
            shell.expect('Password:')
            shell.sendline(pw)
            shell.expect(self.prompt_string)
        return shell

    def import_tar(self, source, name):
        shell = pexpect.spawn('machinectl import-tar %s %s' % (source, name))
        shell.expect("Exiting", timeout = 300)

    def list(self):
        results = pexpect.run('machinectl list')
        results = results.split(b'\r\n')[1:-3]
        results = [ x.split()[0].decode("ascii") for x in results]
        return results

    def list_images(self):
        images = pexpect.run('machinectl list-images')
        images = images.split(b'\r\n')[1:-3]
        images = [ x.split()[0].decode("ascii") for x in images]
        return images

    def remove_image(self, name):
        pexpect.run('machinectl remove %s' % name)

    def clone(self, source, dest):
        pexpect.run('machinectl clone %s %s' % (source, dest))

if __name__ == "__main__":
    ctl = Machinectl()
    ctl.list_images()