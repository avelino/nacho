#!/usr/bin/env python
# -*- coding: utf-8 -*-
from tornado.ioloop import IOLoop
from tornado import autoreload as AutoReload


class NachoServer(IOLoop):
    def run(self):
        return self.instance().start()


def AutoReloadFn():
    print("Hooked before reloading...")
