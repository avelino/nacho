#!/usr/bin/env python3
import logging
import sys

assert sys.version >= '3.3', 'Please use Python 3.3 or higher.'

from nacho.routing import Router
from nacho.http import HttpServer
from nacho.multithreading import Superviser
from nacho.app import Application, StaticFile


class Home(Application):
    def get(self, request_args=None):
        data = {'title': 'Nacho Application Server'}
        self.render('home.html', **data)


def urls():
    router = Router()
    router.add_handler('/static/',
                       StaticFile('/Users/avelino/projects/nacho/example/'))
    router.add_handler('/(.*)', Home())
    return HttpServer(router, debug=True, keep_alive=75)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    superviser = Superviser()
    superviser.start(urls)