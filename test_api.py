#!/
"""
    test_api
    ~~~~~~~~

    Unit testing for the API.

    You can call this script directly, do `$ nosetests` if you've got nose,
    or use the the test command from the manage.py script to run the suite.
"""

import json
from unittest import TestCase
from werkzeug.test import Client
from werkzeug.wrappers import BaseResponse
from werkzeug.exceptions import NotAcceptable, BadRequest

from api.middleware import (
    BeforeAfterMiddleware,
    DataTransformer,
    FieldLimiter,
)


test_data = {'message': 'hello world', 'errors': []}
json_resp = lambda resp: json.loads(resp.get_data(as_text=True))


def dummy_json_app(environ, start_response):
    """Stupid app that sends a deep message: hello world"""
    response = BaseResponse(json.dumps(test_data), mimetype='application/json')
    return response(environ, start_response)


class TestMiddlewareBase(TestCase):

    def test_passthrough_mw(self):
        app = BeforeAfterMiddleware(dummy_json_app)
        c = Client(app, BaseResponse)
        response = c.get('/')
        self.assertEqual(json_resp(response), test_data)


class TestDataTransformer(TestCase):

    def setUp(self):
        self.app = DataTransformer(dummy_json_app)

    def test_accept_json(self):
        c = Client(self.app, BaseResponse)
        resp = c.get('/', headers=[('Accept', 'application/json')])
        self.assertEqual(json_resp(resp), test_data)

    def test_reject_blah(self):
        c = Client(self.app, BaseResponse)
        with self.assertRaises(NotAcceptable):
            resp = c.get('/', headers=[('Accept', 'blah/blah')])


class TestFieldLimiter(TestCase):

    def setUp(self):
        app = FieldLimiter(dummy_json_app)
        self.client = Client(app, BaseResponse)

    def test_no_limiting(self):
        resp = self.client.get('/')
        self.assertEqual(json_resp(resp), test_data)

    def test_limit_one(self):
        resp = self.client.get('/?fields=message')
        self.assertEqual(json_resp(resp), {'message': test_data['message']})

    def test_limit_multi(self):
        fields = ('message', 'errors')
        resp = self.client.get('/?fields={}&fields={}'.format(*fields))
        expecting = {k: v for k, v in test_data.items() if k in fields}
        self.assertEqual(json_resp(resp), expecting)

    def test_limit_bad(self):
        with self.assertRaises(BadRequest):
            resp = self.client.get('/?fields=nonexistentfield')


if __name__ == '__main__':
    from unittest import main
    main()
