#!/usr/bin/env python3
import cgi
import os
import tulip
import tulip.http
import email.message
from urllib.parse import urlparse
from tulip.http.errors import HttpErrorException

from nacho.renderers.quik import QuikWorker


class Application(object):

    template_dirs = ['html']
    http_method_names = ['get', 'post', 'put', 'delete', 'head', 'options', 'trace']

    def __init__(self, write_headers=True):
        self.response = None
        self.write_headers = write_headers
        self.renderer = QuikWorker(self.template_dirs)

    def initialize(self, server, message, payload, prev_response=None):
        self.server = server
        self.request = message
        self.payload = payload
        self.prev_response = prev_response
        if self.write_headers:
            self.response = self._write_headers()

    def __call__(self, request_args=None):
        if self.request.method.lower() in self.http_method_names:
            handler = getattr(self, self.request.method.lower(), None)
            if handler:
                return handler()
        self.response.write(b'nacho: base handler')
        return self.response

    @property
    def query(self):
        parsed = urlparse(self.request.path)
        querydict = cgi.parse_qs(parsed.query)
        for key, value in querydict.items():
            if isinstance(value, list) and len(value) < 2:
                querydict[key] = value[0] if value else None
        return querydict

    def _write_headers(self):
        headers = email.message.Message()
        response = tulip.http.Response(
            self.server.transport, 200, close=True)
        response.add_header('Transfer-Encoding', 'chunked')

        # content encoding
        accept_encoding = headers.get('accept-encoding', '').lower()
        if 'deflate' in accept_encoding:
            response.add_header('Content-Encoding', 'deflate')
            response.add_compression_filter('deflate')
        elif 'gzip' in accept_encoding:
            response.add_header('Content-Encoding', 'gzip')
            response.add_compression_filter('gzip')

        response.add_chunking_filter(1025)

        response.add_header('Content-type', 'text/html')
        response.send_headers()
        return response

    def render(self, template_name, **kwargs):
        self.response.write(self.renderer.render(template_name, **kwargs))


class StaticFile(Application):
    def __init__(self, staticroot):
        super(StaticFile, self).__init__(write_headers=False)
        self.staticroot = staticroot

    def __call__(self, request_args=None):
        path = self.staticroot
        if not os.path.exists(path):
            print('no file', repr(path))
            path = None
        else:
            isdir = os.path.isdir(path)

        if not path:
            raise HttpErrorException(404, message="Path not found")

        headers = email.message.Message()
        response = tulip.http.Response(
            self.server.transport, 200, close=True)
        response.add_header('Transfer-Encoding', 'chunked')

        if isdir:
            response.add_header('Content-type', 'text/html')
            response.send_headers()

            response.write(b'<ul>\r\n')
            for name in sorted(os.listdir(path)):
                if name.isprintable() and not name.startswith('.'):
                    try:
                        bname = name.encode('ascii')
                    except UnicodeError:
                        pass
                    else:
                        if os.path.isdir(os.path.join(path, name)):
                            response.write(b'<li><a href="' + bname +
                                           b'/">' + bname + b'/</a></li>\r\n')
                        else:
                            response.write(b'<li><a href="' + bname +
                                           b'">' + bname + b'</a></li>\r\n')
            response.write(b'</ul>')
        else:
            response.add_header('Content-type', 'text/plain')
            response.send_headers()

            try:
                with open(path, 'rb') as fp:
                    chunk = fp.read(8196)
                    while chunk:
                        response.write(chunk)
                        chunk = fp.read(8196)
            except OSError:
                response.write(b'Cannot open')
        return response
