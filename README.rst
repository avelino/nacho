nacho
=====
Python micro web-framework and asynchronous networking library tulip, support Python 3.x

.. image:: https://raw.github.com/avelino/nacho/master/docs/_static/nacho.png

.. image:: https://drone.io/github.com/avelino/nacho/status.png
    :target: https://drone.io/github.com/avelino/nacho/latest)
    :alt: Build Status - Drone

.. image:: https://travis-ci.org/avelino/nacho.png?branch=master
    :target: https://travis-ci.org/avelino/nacho
    :alt: Build Status - Travis CI


Our goals
=========

- It was designed to work on Python >= 3.3
- tulip is default http server
- Templates are done by **Jinja2**
- HTML5 as the big-main-thing
- Work friendly with NoSQL (otherwise we should stop talking about them)
- Handle asynchronous requests properly


Parameters Server
=================

- **host** - the hostname to listen on. Set this to '0.0.0.0' to have the server available externally as well. Defaults to *'127.0.0.1'*.
- **port** - the port of the webserver. Defaults to *7000* or the port defined in the SERVER_NAME config variable if present.
- **workers** - the workers number. Defaults to *1*.
- **iocp** - the operacional sistem Windows IOCP event loop. Defaults to *False*.
- **ssl** - the ssl mode. Defaults to *False*
