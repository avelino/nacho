#!/usr/bin/env python
# -*- coding: utf-8 -*-
from tornado.web import RequestHandler

from jinja2 import Environment, FileSystemLoader, TemplateNotFound


class ApplicationController(RequestHandler):
    def render(self, template_name, **kwargs):
        kwargs.update({
            'settings': self.settings,
            'STATIC_URL': self.settings.get('static_url_prefix', '/static/'),
            'request': self.request,
            'xsrf_token': self.xsrf_token,
            'xsrf_form_html': self.xsrf_form_html,
        })
        self.write(self.render_template(template_name, **kwargs))

    def render_template(self, template_name, **kwargs):
        template_dirs = []
        if self.settings.get('template_path', ''):
            template_dirs.append(self.settings["template_path"])
        env = Environment(loader=FileSystemLoader(template_dirs))
        try:
            template = env.get_template(template_name)
        except TemplateNotFound:
            raise TemplateNotFound(template_name)
        return template.render(kwargs)
