# -*- coding: utf-8 -*-
from blinker import signal

# core signals.
template_rendered = signal('template-rendered')
request_started = signal('request-started')
request_finished = signal('request-finished')
