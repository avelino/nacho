#!/usr/bin/env python3
import unittest
import unittest.mock
import re

import tulip
from tulip.http import server, errors
from tulip.test_utils import run_briefly
from nacho.http import HttpServer
from nacho.routing import Router


class MockHttpServer(HttpServer):
    """Wrap server class with mocking support
    """
    def handle_error(self, *args, **kwargs):
        if self.transport.__class__.__name__ == 'Mock':
            self.transport.reset_mock()
        super(HttpServer, self).handle_error(*args, **kwargs)


class HttpServerTest(unittest.TestCase):
    def setUp(self):
        self.loop = tulip.new_event_loop()
        tulip.set_event_loop(self.loop)

    def tearDown(self):
        self.loop.close()

    def test_handle_request(self):
        transport = unittest.mock.Mock()
        srv = MockHttpServer(Router())
        srv.connection_made(transport)
        rline = unittest.mock.Mock()
        rline.version = (1, 1)
        message = unittest.mock.Mock()
        srv.handle_request(rline, message)
        srv.stream.feed_data(
            b'GET / HTTP/1.0\r\n'
            b'Host: example.com\r\n\r\n')
        self.loop.run_until_complete(srv._request_handler)

        content = b''.join([c[1][0] for c in list(transport.write.mock_calls)])
        self.assertTrue(content.startswith(b'HTTP/1.1 404 Not Found\r\n'))

    def _base_handler_test(self, urlregx, handler, testcontent, url=b'/',
                           expected_code=200):
        transport = unittest.mock.Mock()
        router = Router()
        router.add_handler(
            urlregx, handler)
        srv = MockHttpServer(router)
        srv.connection_made(transport)
        rline = unittest.mock.Mock()
        rline.version = (1, 1)
        message = unittest.mock.Mock()
        srv.handle_request(rline, message)
        srv.stream.feed_data(b'GET ')
        srv.stream.feed_data(url)
        srv.stream.feed_data(b' HTTP/1.0\r\n'
            b'Host: example.com\r\n\r\n')
        self.loop.run_until_complete(srv._request_handler)

        header = transport.write.mock_calls[0][1][0].decode('utf-8')
        code = int(re.match("^HTTP/1.1 (\d+) ", header).groups()[0])
        self.assertEquals(code, expected_code, )
        headers = re.findall(r"(?P<name>.*?): (?P<value>.*?)\r\n", header)
        content = b''.join([c[1][0] for c in list(transport.write.mock_calls)[2:-2]])
        self.assertEqual(content, testcontent)
        transport = None


class HttpServerProtocolTests(unittest.TestCase):

    def setUp(self):
        self.loop = tulip.new_event_loop()
        tulip.set_event_loop(self.loop)

    def tearDown(self):
        self.loop.close()

    def test_http_status_exception(self):
        exc = errors.HttpErrorException(500, message='Internal error')
        self.assertEqual(exc.code, 500)
        self.assertEqual(exc.message, 'Internal error')

    def test_handle_request(self):
        transport = unittest.mock.Mock()

        srv = server.ServerHttpProtocol()
        srv.connection_made(transport)

        rline = unittest.mock.Mock()
        rline.version = (1, 1)
        message = unittest.mock.Mock()
        srv.handle_request(rline, message)

        content = b''.join([c[1][0] for c in list(transport.write.mock_calls)])
        self.assertTrue(content.startswith(b'HTTP/1.1 404 Not Found\r\n'))

    def test_connection_made(self):
        srv = server.ServerHttpProtocol()
        self.assertIsNone(srv._request_handler)

        srv.connection_made(unittest.mock.Mock())
        self.assertIsNotNone(srv._request_handler)

    def test_data_received(self):
        srv = server.ServerHttpProtocol()
        srv.connection_made(unittest.mock.Mock())

        srv.data_received(b'123')
        self.assertEqual(b'123', bytes(srv.stream._buffer))

        srv.data_received(b'456')
        self.assertEqual(b'123456', bytes(srv.stream._buffer))

    def test_eof_received(self):
        srv = server.ServerHttpProtocol()
        srv.connection_made(unittest.mock.Mock())
        srv.eof_received()
        self.assertTrue(srv.stream._eof)

    def test_connection_lost(self):
        srv = server.ServerHttpProtocol()
        srv.connection_made(unittest.mock.Mock())
        srv.data_received(b'123')

        keep_alive_handle = srv._keep_alive_handle = unittest.mock.Mock()

        handle = srv._request_handler
        srv.connection_lost(None)

        self.assertIsNone(srv._request_handler)
        self.assertTrue(handle.cancelled())

        self.assertIsNone(srv._keep_alive_handle)
        self.assertTrue(keep_alive_handle.cancel.called)

        srv.connection_lost(None)
        self.assertIsNone(srv._request_handler)
        self.assertIsNone(srv._keep_alive_handle)

    def test_srv_keep_alive(self):
        srv = server.ServerHttpProtocol()
        self.assertFalse(srv._keep_alive)

        srv.keep_alive(True)
        self.assertTrue(srv._keep_alive)

        srv.keep_alive(False)
        self.assertFalse(srv._keep_alive)

    def test_handle_error(self):
        transport = unittest.mock.Mock()
        srv = server.ServerHttpProtocol()
        srv.connection_made(transport)
        srv.keep_alive(True)

        srv.handle_error(404, headers=(('X-Server', 'Tulip'),))
        content = b''.join([c[1][0] for c in list(transport.write.mock_calls)])
        self.assertIn(b'HTTP/1.1 404 Not Found', content)
        self.assertIn(b'X-SERVER: Tulip', content)
        self.assertFalse(srv._keep_alive)

    @unittest.mock.patch('tulip.http.server.traceback')
    def test_handle_error_traceback_exc(self, m_trace):
        transport = unittest.mock.Mock()
        log = unittest.mock.Mock()
        srv = server.ServerHttpProtocol(debug=True, log=log)
        srv.connection_made(transport)

        m_trace.format_exc.side_effect = ValueError

        srv.handle_error(500, exc=object())
        content = b''.join([c[1][0] for c in list(transport.write.mock_calls)])
        self.assertTrue(
            content.startswith(b'HTTP/1.1 500 Internal Server Error'))
        self.assertTrue(log.exception.called)

    def test_handle_error_debug(self):
        transport = unittest.mock.Mock()
        srv = server.ServerHttpProtocol()
        srv.debug = True
        srv.connection_made(transport)

        try:
            raise ValueError()
        except Exception as exc:
            srv.handle_error(999, exc=exc)

        content = b''.join([c[1][0] for c in list(transport.write.mock_calls)])

        self.assertIn(b'HTTP/1.1 500 Internal', content)
        self.assertIn(b'Traceback (most recent call last):', content)

    def test_handle_error_500(self):
        log = unittest.mock.Mock()
        transport = unittest.mock.Mock()

        srv = server.ServerHttpProtocol(log=log)
        srv.connection_made(transport)

        srv.handle_error(500)
        self.assertTrue(log.exception.called)

    def test_handle(self):
        transport = unittest.mock.Mock()
        srv = server.ServerHttpProtocol()
        srv.connection_made(transport)

        handle = srv.handle_request = unittest.mock.Mock()

        srv.stream.feed_data(
            b'GET / HTTP/1.0\r\n'
            b'Host: example.com\r\n\r\n')

        self.loop.run_until_complete(srv._request_handler)
        self.assertTrue(handle.called)
        self.assertTrue(transport.close.called)

    def test_handle_coro(self):
        transport = unittest.mock.Mock()
        srv = server.ServerHttpProtocol()

        called = False

        @tulip.coroutine
        def coro(message, payload):
            nonlocal called
            called = True
            srv.eof_received()

        srv.handle_request = coro
        srv.connection_made(transport)

        srv.stream.feed_data(
            b'GET / HTTP/1.0\r\n'
            b'Host: example.com\r\n\r\n')
        self.loop.run_until_complete(srv._request_handler)
        self.assertTrue(called)

    def test_handle_cancel(self):
        log = unittest.mock.Mock()
        transport = unittest.mock.Mock()

        srv = server.ServerHttpProtocol(log=log, debug=True)
        srv.connection_made(transport)

        srv.handle_request = unittest.mock.Mock()

        @tulip.task
        def cancel():
            srv._request_handler.cancel()

        self.loop.run_until_complete(
            tulip.wait([srv._request_handler, cancel()]))
        self.assertTrue(log.debug.called)

    def test_handle_cancelled(self):
        log = unittest.mock.Mock()
        transport = unittest.mock.Mock()

        srv = server.ServerHttpProtocol(log=log, debug=True)
        srv.connection_made(transport)

        srv.handle_request = unittest.mock.Mock()
        run_briefly(self.loop)  # start request_handler task

        srv.stream.feed_data(
            b'GET / HTTP/1.0\r\n'
            b'Host: example.com\r\n\r\n')

        r_handler = srv._request_handler
        srv._request_handler = None  # emulate srv.connection_lost()

        self.assertIsNone(self.loop.run_until_complete(r_handler))

    def test_handle_400(self):
        transport = unittest.mock.Mock()
        srv = server.ServerHttpProtocol()
        srv.connection_made(transport)
        srv.handle_error = unittest.mock.Mock()
        srv.keep_alive(True)
        srv.stream.feed_data(b'GET / HT/asd\r\n\r\n')

        self.loop.run_until_complete(srv._request_handler)
        self.assertTrue(srv.handle_error.called)
        self.assertTrue(400, srv.handle_error.call_args[0][0])
        self.assertTrue(transport.close.called)

    def test_handle_500(self):
        transport = unittest.mock.Mock()
        srv = server.ServerHttpProtocol()
        srv.connection_made(transport)

        handle = srv.handle_request = unittest.mock.Mock()
        handle.side_effect = ValueError
        srv.handle_error = unittest.mock.Mock()

        srv.stream.feed_data(
            b'GET / HTTP/1.0\r\n'
            b'Host: example.com\r\n\r\n')
        self.loop.run_until_complete(srv._request_handler)

        self.assertTrue(srv.handle_error.called)
        self.assertTrue(500, srv.handle_error.call_args[0][0])

    def test_handle_error_no_handle_task(self):
        transport = unittest.mock.Mock()
        srv = server.ServerHttpProtocol()
        srv.keep_alive(True)
        srv.connection_made(transport)
        srv.connection_lost(None)

        srv.handle_error(300)
        self.assertFalse(srv._keep_alive)

    def test_keep_alive(self):
        srv = server.ServerHttpProtocol(keep_alive=0.1)
        transport = unittest.mock.Mock()
        closed = False

        def close():
            nonlocal closed
            closed = True
            srv.connection_lost(None)
            self.loop.stop()

        transport.close = close

        srv.connection_made(transport)

        handle = srv.handle_request = unittest.mock.Mock()

        srv.stream.feed_data(
            b'GET / HTTP/1.1\r\n'
            b'CONNECTION: keep-alive\r\n'
            b'HOST: example.com\r\n\r\n')

        self.loop.run_forever()
        self.assertTrue(handle.called)
        self.assertTrue(closed)

    def test_keep_alive_close_existing(self):
        transport = unittest.mock.Mock()
        srv = server.ServerHttpProtocol(keep_alive=15)
        srv.connection_made(transport)

        self.assertIsNone(srv._keep_alive_handle)
        keep_alive_handle = srv._keep_alive_handle = unittest.mock.Mock()
        srv.handle_request = unittest.mock.Mock()

        srv.stream.feed_data(
            b'GET / HTTP/1.0\r\n'
            b'HOST: example.com\r\n\r\n')

        self.loop.run_until_complete(srv._request_handler)
        self.assertTrue(keep_alive_handle.cancel.called)
        self.assertIsNone(srv._keep_alive_handle)
        self.assertTrue(transport.close.called)
