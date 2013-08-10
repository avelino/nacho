# -*- coding: utf-8 -*-
from contextlib import contextmanager
from tornado.testing import AsyncTestCase, AsyncHTTPTestCase, AsyncHTTPSTestCase
from nacho.signals import template_rendered


class CapturedTemplatesMixin(object):
    @contextmanager
    def captured_templates(self):
        recorded = []

        def record(sender, template, context, **extra):
            recorded.append((template, context))

        template_rendered.connect(record)

        try:
            yield recorded
        finally:
            template_rendered.disconnect(record)


class NachoAsyncTestCase(AsyncTestCase, CapturedTemplatesMixin):
    pass


class NachoAsyncHTTPTestCase(AsyncHTTPTestCase, CapturedTemplatesMixin):
    pass


class NachoAsyncHTTPSTestCase(AsyncHTTPSTestCase, CapturedTemplatesMixin):
    pass
