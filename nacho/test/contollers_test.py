#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
from tornado.testing import AsyncHTTPTestCase, ExpectLog
from tornado.test.util import unittest
from tornado.template import DictLoader

from nacho.services.routers import Routers
from nacho.controllers.base import ApplicationController


wsgi_safe_tests = []


def wsgi_safe(cls):
    wsgi_safe_tests.append(cls)
    return cls


class WebTestCase(AsyncHTTPTestCase):
    def get_app(self):
        self.app = Routers(
            self.get_handlers(),
            template_path=os.path.join(os.path.dirname(__file__), "views"),
            **self.get_app_kwargs())
        return self.app

    def get_handlers(self):
        raise NotImplementedError()

    def get_app_kwargs(self):
        return {}


class SimpleHandlerTestCase(WebTestCase):
    def get_handlers(self):
        return [('/', self.Handler)]


@wsgi_safe
class ControllerMethodRenderTest(SimpleHandlerTestCase):
    class Handler(ApplicationController):
        def get(self):
            self.render('foo.html', **{'engine': 'Jinja2'})

    def tearDown(self):
        super(ControllerMethodRenderTest, self).tearDown()
        ApplicationController._template_loaders.clear()

    def test_render_method(self):
        response = self.fetch('/')
        self.assertEqual(response.body,
                         b'Nacho used template engine Jinja2')
        self.assertEqual(response.code, 200)


if __name__ == '__main__':
    unittest.main()
