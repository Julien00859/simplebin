#!/usr/bin/env python3

import collections
import random
import string
import urllib.parse
import traceback
from pathlib import Path
from wsgiref.util import setup_testing_defaults
from wsgiref.simple_server import make_server, demo_app


#
#  Configuration
#

HOST = 'localhost'
PORT = 8000

root = Path(__file__).parent
storage = root.joinpath('storage')
storage.mkdir(exist_ok=True)


#
#  Templates
#

bin_html_form = b"""\
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>simplebin</title>
</head>
<body>
  <form name=binform action="/create" method=POST accept-charset=utf-8>
    <textarea spellcheck=false placeholder="Entrez votre code ici" rows=12 cols=60 name=code></textarea>
    <p><input type=submit></p>
  </form>
</body>
</html>
"""


#
#  Router
#

router = {}
Endpoint = collections.namedtuple('Endpoint', ('func', 'methods', 'path'))
def route(path, methods=['GET']):
    return lambda func: router.setdefault(path, Endpoint(func, methods, path))

def application(environ, start_response):
    setup_testing_defaults(environ)

    endpoint = router.get(environ['PATH_INFO'])
    if not endpoint:
        payload = f"{environ['PATH_INFO']!r} not found.".encode()
        start_response('404 Not Found', [
            ('Content-Type', 'text/plain; charset=utf-8'),
            ('Content-Length', str(len(payload))),
        ])
        return [payload]

    if environ['REQUEST_METHOD'] not in endpoint.methods:
        payload = f"{environ['PATH_INFO']!r} is only compatible with {endpoint.methods} methods.".encode()
        start_response('405 Method Not Allowed', [
            ('Content-Type', 'text/plain; charset=utf-8'),
            ('Content-Length', str(len(payload))),
        ])
        return [payload]

    try:
        return endpoint.func(environ, start_response)  # The endpoint is called here
    except AssertionError as exc:
        payload = exc.args[0].encode()
        start_response(exc.args[0], [
            ('Content-Type', 'text/plain; charset=utf-8'),
            ('Content-Length', str(len(payload))),
        ])
        return [payload]
    except Exception as exc:
        traceback.print_exc()
        payload = f"Internal Server Error: {exc}".encode()
        start_response("500 Internal Server Error", [
            ('Content-Type', 'text/plain; charset=utf-8'),
            ('Content-Length', str(len(payload))),
        ])
        return [payload]


#
#  Database
#

class Snippet:
    def __init__(self, id, code):
        self.id = id
        self.code = code

    @property
    def url(self):
        return f'http://{HOST}:{PORT}/show?id={self.id}'

    @staticmethod
    def new_id(length=6):
        id = "".join([
            random.choice(string.ascii_lowercase)
            for _ in range(length)
        ])
        if storage.joinpath(id).exists():
            raise ValueError("Cannot create a new unique id.")
        return id

    def save(self):
        storage.joinpath(self.id).write_text(self.code)

    @classmethod
    def get_by_id(cls, id):
        code = storage.joinpath(id).read_text()
        return cls(id, code)


#
#  API
#

@route('/')
def bin_form(environ, start_response):
    start_response('200 OK', [
        ('Content-Type', 'text/html; charset=utf-8'),
        ('Content-Length', str(len(bin_html_form))),
    ])
    return [bin_html_form]


@route('/status')
def status(_environ, start_response):
    start_response('200 Ok', [])
    return []


@route('/create', methods=['POST'])
def save_bin(environ, start_response):
    # Quick and dirty header parsing, there still isn't anything in the
    # python stdlib to parse http headers.
    content_length = int(environ.get('CONTENT_LENGTH', '1024'))
    content_type = environ.get('CONTENT_TYPE')
    mimetype = content_type.partition(';')[0] or 'application/x-www-form-urlencoded'
    charset = content_type.partition('charset=')[2].partition(';')[0] or 'utf-8'

    # Those checks could be safer but... heh... let's keep it simple :)
    assert content_length < (1 << 20), "413 Payload Too Large"
    assert mimetype == 'application/x-www-form-urlencoded', "415 Unsupported Media Type"

    # Actual form extraction
    body = environ['wsgi.input'].read(content_length).decode(charset)
    form = urllib.parse.parse_qs(body)

    snippet = Snippet(Snippet.new_id(), form['code'][0])
    snippet.save()

    start_response('303 See Other', [
        ('Location', snippet.url)
    ])
    return []

@route('/show')
def show_bin(environ, start_response):
    qs = urllib.parse.parse_qs(environ['QUERY_STRING'])

    try:
        snippet = Snippet.get_by_id(qs['id'][0])
    except FileNotFoundError:
        assert False, "404 Not Found"

    start_response('200 OK', [
        ('Content-Type', 'text/plain; charset=utf-8'),
        ('Content-Length', str(len(snippet.code)))
    ])
    return [snippet.code.encode()]


#
#  Server
#

def main():
    print(f"Listening on http://{HOST}:{PORT}/")
    print("Press ctrl-c to stop")
    with make_server(HOST, PORT, application) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == '__main__':
    main()
