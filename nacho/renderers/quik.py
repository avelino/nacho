#!/usr/bin/env python3
from quik import CachingFileLoader


class QuikWorker(object):

    def __init__(self, template_dirs=['html']):
        self.template_dirs = template_dirs

    def render(self, template_name, *args, **kwargs):
        loader = CachingFileLoader(self.template_dirs[0])
        template = loader.load_template(template_name)
        return template.merge(kwargs, loader=loader).encode('utf-8')
