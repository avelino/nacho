#!/usr/bin/env python3
import os
import socket
import signal
import time
import tulip
import argparse
import tulip.http
from tulip.http import websocket
try:
    import ssl
except ImportError:  # pragma: no cover
    ssl = None


ARGS = argparse.ArgumentParser(description="Run simple http server.")
ARGS.add_argument(
    '--host', action="store", dest='host',
    default='127.0.0.1', help='Host name')
ARGS.add_argument(
    '--port', action="store", dest='port',
    default=7000, type=int, help='Port number')
ARGS.add_argument(
    '--iocp', action="store_true", dest='iocp', help='Windows IOCP event loop')
ARGS.add_argument(
    '--ssl', action="store_true", dest='ssl', help='Run ssl mode.')
ARGS.add_argument(
    '--sslcert', action="store", dest='certfile', help='SSL cert file.')
ARGS.add_argument(
    '--sslkey', action="store", dest='keyfile', help='SSL key file.')
ARGS.add_argument(
    '--workers', action="store", dest='workers',
    default=1, type=int, help='Number of workers.')
ARGS.add_argument(
    '--staticroot', action="store", dest='staticroot',
    default='./static/', type=str, help='Static root.')


class ChildProcess:

    def __init__(self, up_read, down_write, args, sock, protocol_factory, ssl):
        self.up_read = up_read
        self.down_write = down_write
        self.args = args
        self.sock = sock
        self.protocol_factory = protocol_factory
        self.ssl = ssl

    def start(self):
        # start server
        self.loop = loop = tulip.new_event_loop()
        tulip.set_event_loop(loop)

        def stop():
            self.loop.stop()
            os._exit(0)
        loop.add_signal_handler(signal.SIGINT, stop)

        f = loop.start_serving(
            self.protocol_factory, sock=self.sock, ssl=self.ssl)
        x = loop.run_until_complete(f)[0]
        print('Starting srv worker process {} on {}'.format(
            os.getpid(), x.getsockname()))

        # heartbeat
        self.heartbeat()

        tulip.get_event_loop().run_forever()
        os._exit(0)

    @tulip.task
    def heartbeat(self):
        # setup pipes
        read_transport, read_proto = yield from self.loop.connect_read_pipe(
            tulip.StreamProtocol, os.fdopen(self.up_read, 'rb'))
        write_transport, _ = yield from self.loop.connect_write_pipe(
            tulip.StreamProtocol, os.fdopen(self.down_write, 'wb'))

        reader = read_proto.set_parser(websocket.WebSocketParser())
        writer = websocket.WebSocketWriter(write_transport)

        while True:
            msg = yield from reader.read()
            if msg is None:
                print('Superviser is dead, {} stopping...'.format(os.getpid()))
                self.loop.stop()
                break
            elif msg.tp == websocket.MSG_PING:
                writer.pong()
            elif msg.tp == websocket.MSG_CLOSE:
                break

        read_transport.close()
        write_transport.close()


class Worker:

    _started = False

    def __init__(self, loop, args, sock, protocol_factory, ssl):
        self.loop = loop
        self.args = args
        self.sock = sock
        self.protocol_factory = protocol_factory
        self.ssl = ssl
        self.start()

    def start(self):
        assert not self._started
        self._started = True

        up_read, up_write = os.pipe()
        down_read, down_write = os.pipe()
        args, sock = self.args, self.sock

        pid = os.fork()
        if pid:
            # parent
            os.close(up_read)
            os.close(down_write)
            self.connect(pid, up_write, down_read)
        else:
            # child
            os.close(up_write)
            os.close(down_read)

            # cleanup after fork
            tulip.set_event_loop(None)

            # setup process
            process = ChildProcess(up_read, down_write, args, sock, 
                                   self.protocol_factory, self.ssl)
            process.start()

    @tulip.task
    def heartbeat(self, writer):
        while True:
            yield from tulip.sleep(15)

            if (time.monotonic() - self.ping) < 30:
                writer.ping()
            else:
                print('Restart unresponsive worker process: {}'.format(
                    self.pid))
                self.kill()
                self.start()
                return

    @tulip.task
    def chat(self, reader):
        while True:
            msg = yield from reader.read()
            if msg is None:
                print('Restart unresponsive worker process: {}'.format(
                    self.pid))
                self.kill()
                self.start()
                return
            elif msg.tp == websocket.MSG_PONG:
                self.ping = time.monotonic()

    @tulip.task
    def connect(self, pid, up_write, down_read):
        # setup pipes
        read_transport, proto = yield from self.loop.connect_read_pipe(
            tulip.StreamProtocol, os.fdopen(down_read, 'rb'))
        write_transport, _ = yield from self.loop.connect_write_pipe(
            tulip.StreamProtocol, os.fdopen(up_write, 'wb'))

        # websocket protocol
        reader = proto.set_parser(websocket.WebSocketParser())
        writer = websocket.WebSocketWriter(write_transport)

        # store info
        self.pid = pid
        self.ping = time.monotonic()
        self.rtransport = read_transport
        self.wtransport = write_transport
        self.chat_task = self.chat(reader)
        self.heartbeat_task = self.heartbeat(writer)

    def kill(self):
        self._started = False
        self.chat_task.cancel()
        self.heartbeat_task.cancel()
        self.rtransport.close()
        self.wtransport.close()
        os.kill(self.pid, signal.SIGTERM)


class Superviser:

    def __init__(self):
        self.loop = tulip.get_event_loop()
        args = ARGS.parse_args()
        if ':' in args.host:
            args.host, port = args.host.split(':', 1)
            args.port = int(port)

        if args.iocp:
            from tulip import windows_events
            sys.argv.remove('--iocp')
            logging.info('using iocp')
            el = windows_events.ProactorEventLoop()
            tulip.set_event_loop(el)

        if args.ssl:
            here = os.path.join(os.path.dirname(__file__), 'tests')

            if args.certfile:
                certfile = args.certfile or os.path.join(here, 'sample.crt')
                keyfile = args.keyfile or os.path.join(here, 'sample.key')
            else:
                certfile = os.path.join(here, 'sample.crt')
                keyfile = os.path.join(here, 'sample.key')

            sslcontext = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
            sslcontext.load_cert_chain(certfile, keyfile)
        else:
            sslcontext = None
        self.ssl = sslcontext

        self.args = args
        self.workers = []

    def start(self, protocol_factory):
        # bind socket
        sock = self.sock = socket.socket()
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((self.args.host, self.args.port))
        sock.listen(1024)
        sock.setblocking(False)

        # start processes
        for idx in range(self.args.workers):
            self.workers.append(Worker(self.loop, self.args, sock, protocol_factory, self.ssl))

        self.loop.add_signal_handler(signal.SIGINT, lambda: self.loop.stop())
        self.loop.run_forever()
