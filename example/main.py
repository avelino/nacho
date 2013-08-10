#!/usr/bin/env python
# -*- coding: utf-8 -*-
from nacho.services import servers
from nacho.controllers.base import ApplicationController


class Home(ApplicationController):
    def get(self):
        self.render("views/home.html")


class Application(servers.NachoServer):
    def __init__(self):
        urls = [
            (r"/", Home)
        ]
        settings = dict(
            xsrf_cookies=True,
            xheaders=True,
        )
        servers.NachoServer.__init__(self, urls, settings)
