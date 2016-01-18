#!/usr/bin/env python3

import pexpect

class Machinectl(object):
    def __init__(self):
        pass

    def start(self, name):
        pexpect.run('machinectl start %s' % name)

    def login(self, name):
        return pexpect.spawn('machinectl login %s' % name)

    def import_tar(self, source, name):
        shell = pexpect.spawn('machinectl import-tar %s %s' % (source, name))
        shell.expect("Exiting")

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