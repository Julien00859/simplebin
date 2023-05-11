import urllib.request
import unittest
from threading import Thread

import simplebin
import bottle


BASE_URL = f'http://{simplebin.HTTP_HOST}:{simplebin.HTTP_PORT}'
def urlopen(path):
    try:
        res = urllib.request.urlopen(urllib.parse.urljoin(BASE_URL, path))
        return res
    except urllib.error.HTTPError as res:
        return res


class TestSimpleBin(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        print("Starting builtin server in a daemon thread")
        threaded_server = Thread(target=bottle.run, daemon=True, kwargs={
            'host': simplebin.HTTP_HOST,
            'port': simplebin.HTTP_PORT,
            'quiet': True,
        })
        threaded_server.start()
        threaded_server.join(.5)  # quick and dirty


    def test_get_snippet(self):
        """ Accessing a snippet that exist show the valid code """
        import unittest.mock
        snippet = simplebin.Snippet('iexist', 'Hello world')
        with unittest.mock.patch('simplebin.Snippet') as mock:
            mock.get_by_name.return_value = snippet
            with urlopen('/iexist') as res:
                self.assertEqual(res.status, 200)
                self.assertEqual(res.read().decode(), "Hello world")


    def test_missing_snippet(self):
        """ Accessing a snippet that does not exist fails with a 404 """
        import unittest.mock
        snippet = simplebin.Snippet('Snippet idontexist! not found', '404')
        with unittest.mock.patch('simplebin.Snippet') as mock:
            mock.get_by_name.side_effect = ValueError()
            with urlopen('/idontexist') as res:
                self.assertEqual(res.status, 404)


if __name__ == '__main__':
    unittest.main()
