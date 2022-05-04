import unittest
from threading import Thread
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.parse import urljoin
from urllib.request import urlopen

import simplebin

BASE_URL = f'http://{simplebin.HOST}:{simplebin.PORT}'


class TestSimpleBin(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print("Starting builtin server in a daemon thread")

        th = Thread(target=simplebin.main, daemon=True)
        th.start()

        # Wait up to 5 seconds for the server to boot
        for i in range(10):
            th.join(.5)
            try:
                urlopen(urljoin(BASE_URL, '/status'))
            except ConnectionRefusedError:
                if i == 9:
                    raise
            else:
                break

    def test_status(self):
        """ Ensure the /status page always works """
        with urlopen(urljoin(BASE_URL, '/status')) as res:
            self.assertEqual(res.status, 204)

    def test_show_snippet(self):
        """ Accessing a snippet that exist show the valid code """

        # Il manque du code ici pour mock la base de donnée...
        # voir https://docs.python.org/3/library/unittest.mock.html
        # peut-être utiliser unittest.mock.patch... avec un return_code...

        with urlopen(urljoin(BASE_URL, '/show?id=iexist')) as res:
            self.assertEqual(res.status, 200)
            self.assertEqual(res.read().decode(), "Hello world")

    def test_missing_snippet(self):
        """ Accessing a snippet that does not exist fails with a 404 """

        # Il manque du code ici pour mock la base de donnée...
        # voir https://docs.python.org/3/library/unittest.mock.html
        # peut-être utiliser unittest.mock.patch... avec un side_effect...

        with self.assertRaises(HTTPError) as exc:
            urlopen(urljoin(BASE_URL, '/show?id=idontexist'))
        self.assertEqual(exc.exception.code, 404)

if __name__ == '__main__':
    unittest.main()
