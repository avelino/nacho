#!/usr/bin/env python3
from jinja2 import Environment, FileSystemLoader, TemplateNotFound


class Jinja2Worker(object):

    def __init__(self, template_dirs=['html']):
        self.template_dirs = template_dirs

    def render(self, template_name, *args, **kwargs):
        env = Environment(loader=FileSystemLoader(self.template_dirs))
        try:
            template = env.get_template(template_name)
        except TemplateNotFound:
            raise TemplateNotFound(template_name)

        return template.render(kwargs).encode('utf-8')
