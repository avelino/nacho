#!/usr/bin/env python3
from quik import FileLoader


class QuikWorker(object):

    def __init__(self, template_dirs=['html']):
        self.template_dirs = template_dirs

    def render(self, template_name, *args, **kwargs):
        loader = FileLoader(self.template_dirs[0])
        template = loader.load_template(template_name)
        return template.render(kwargs, loader=loader).encode('utf-8')
