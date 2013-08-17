#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
from nacho.services.servers import NachoServer, AutoReload, AutoReloadFn
from nacho.services.routers import Routers
from nacho.controllers.base import ApplicationController


class MainHandler(ApplicationController):
    def get(self):
        data = {'title': 'testing'}
        self.render("home.html", **data)


r = Routers(
    [
        (r"/", MainHandler),
    ],
    template_path=os.path.join(os.path.dirname(__file__), "views"),
    debug=True
)


if __name__ == "__main__":
    r.listen(8888)
    AutoReload.add_reload_hook(AutoReloadFn)
    AutoReload.start()
    server = NachoServer()
    server.run()
