#!/usr/bin/env python3

import random
import string
import sys
from pathlib import Path

ROOT_PATH = Path(__file__).parent
sys.path.append(ROOT_PATH)
import bottle
bottle.TEMPLATE_PATH = [ROOT_PATH]


###  Configuration ###

HTTP_HOST = 'localhost'
HTTP_PORT = 8000
DEFAULT_NAME_LENGTH = 6
STORAGE_PATH = ROOT_PATH.joinpath('storage')
STORAGE_PATH.mkdir(exist_ok=True)


### Storage ###

class Snippet:
    def __init__(self, name, code):
        self.name = name
        self.code = code

    @classmethod
    def get_by_name(cls, name):
        try:
            code = STORAGE_PATH.joinpath(name).read_text()
        except FileNotFoundError as exc:
            raise ValueError(f"Snippet {name!r} not found") from exc
        return cls(name, code)

    def save(self):
        STORAGE_PATH.joinpath(self.name).write_text(self.code)

    @staticmethod
    def new_name(length=DEFAULT_NAME_LENGTH):
        name = ''.join(random.choices(string.ascii_letters, k=length))
        if STORAGE_PATH.joinpath(name).exists():
            raise ValueError("Cannot create a new unique id.")
        return name


### API ###

@bottle.route('/status')
def status():
    return "alive"

@bottle.route('/')
def new():
    return bottle.template('newbin')  # newbin.tpl

@bottle.route('/<name>') 
def get(name):
    try:
        snippet = Snippet.get_by_name(name)
    except ValueError:
        bottle.abort(404, "Snippet not found")
    return snippet.code

@bottle.route('/save', method='POST')
def save():
    snippet = Snippet(Snippet.new_name(), bottle.request.forms.code)
    snippet.save()
    return bottle.redirect(f'/{snippet.name}')


### Server ###

if __name__ == '__main__':
    bottle.run(host=HTTP_HOST, port=HTTP_PORT)
