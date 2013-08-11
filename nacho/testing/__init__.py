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

    def assertRedirects(self, response, location):
        self.assertTrue(response.code in (301, 302))
        self.assertEqual(response.headers['Location'], location)

    def assertStatus(self, response, status_code):
        self.assertEqual(response.code, status_code)


class NachoAsyncTestCase(AsyncTestCase, CapturedTemplatesMixin):
    pass


class NachoAsyncHTTPTestCase(AsyncHTTPTestCase, CapturedTemplatesMixin):
    pass


class NachoAsyncHTTPSTestCase(AsyncHTTPSTestCase, CapturedTemplatesMixin):
    pass
