#!/usr/bin/env python3
import tulip
import tulip.http
import email.message
from urllib.parse import urlparse
import cgi

from jinja2 import Environment, FileSystemLoader, TemplateNotFound


class Application(object):

    template_dirs = ['html']
    http_method_names = ['get', 'post', 'put', 'delete', 'head', 'options', 'trace']

    def __init__(self, write_headers=True):
        self.response = None
        self.write_headers = write_headers

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
        env = Environment(loader=FileSystemLoader(self.template_dirs))
        try:
            template = env.get_template(template_name)
        except TemplateNotFound:
            raise TemplateNotFound(template_name)
        self.response.write(template.render(kwargs).encode('utf-8'))
