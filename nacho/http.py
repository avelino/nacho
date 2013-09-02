#!/usr/bin/env python3
import logging

import tulip
from tulip.http import ServerHttpProtocol
from tulip.http.errors import HttpErrorException

class HttpServer(ServerHttpProtocol):
    def __init__(self, router, *args, **kwargs):
        super(HttpServer, self).__init__(*args, **kwargs)
        self.router = router

    @tulip.coroutine
    def handle_request(self, message, payload):
        response = None
        logging.debug('method = {!r}; path = {!r}; version = {!r}'.format(
            message.method, message.path, message.version))

        handlers, args = self.router.get_handler(message.path)
        if handlers:
            for handler in handlers:
                logging.debug("handler: %s", handler)
                handler.initialize(self, message, payload, prev_response=response)
                result = handler(request_args=args)
                response = handler.response
            if not response:
                raise HttpErrorException(404, message="No Handler found")
        else:
            raise HttpErrorException(404)

        response.write_eof()
        if response.keep_alive():
            self.keep_alive(True)
