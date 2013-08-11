#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
from tornado.test.util import unittest
from nacho.testing import NachoAsyncHTTPTestCase
from nacho.services.routers import Routers
from nacho.controllers.base import ApplicationController


class IndexTestHandler(ApplicationController):
    
    def get(self):
        self.render('foo.html', name='chuck norris')


class RedirectTestHandler(ApplicationController):
    def get(self):
        self.redirect('/')


class TestingTestCase(NachoAsyncHTTPTestCase):
    
    def get_app(self):
        self.app = Routers(
            [
                (r'/', IndexTestHandler),
                (r'/redirect', RedirectTestHandler),
            ],
            template_path=os.path.join(os.path.dirname(__file__), 'views'),
        )
        return self.app

    def test_captured_templates(self):
        with self.captured_templates() as templates:
            resp = self.fetch('/')
            template, context = templates[0]
            self.assertEqual(resp.code, 200)
            self.assertEqual(template.name, 'foo.html')
            self.assertEqual(context['name'], 'chuck norris')

    def test_assert_redirects(self):
        resp = self.fetch('/redirect', follow_redirects=False)
        self.assertRedirects(resp, '/')

    def test_assert_status(self):
        resp = self.fetch('/')
        self.assertStatus(resp, 200)

        resp = self.fetch('/redirect', follow_redirects=False)
        self.assertStatus(resp, 302)

        resp = self.fetch('/404')
        self.assertStatus(resp, 404)


if __name__ == '__main__':
    unittest.main()
