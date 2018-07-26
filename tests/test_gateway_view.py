# -*- coding: UTF-8 -*-
"""
A suite of tests for the GatewayView object
"""
import unittest
from unittest.mock import patch, MagicMock

import ujson
from flask import Flask
from vlab_api_common import flask_common
from vlab_api_common.http_auth import generate_test_token


from vlab_gateway_api.lib.views import gateway_view


class TestGatewayView(unittest.TestCase):
    """A set of test cases for the GatewayView object"""
    @classmethod
    def setUpClass(cls):
        """Runs once for the whole test suite"""
        cls.token = generate_test_token(username='bob')

    @classmethod
    def setUp(cls):
        """Runs before every test case"""
        app = Flask(__name__)
        gateway_view.GatewayView.register(app)
        app.config['TESTING'] = True
        cls.app = app.test_client()
        # Mock Celery
        app.celery_app = MagicMock()
        cls.fake_task = MagicMock()
        cls.fake_task.id = 'asdf-asdf-asdf'
        app.celery_app.send_task.return_value = cls.fake_task

    def test_get_task(self):
        """GatewayView - GET on /api/1/inf/gateway returns a task-id"""
        resp = self.app.get('/api/1/inf/gateway',
                            headers={'X-Auth': self.token})

        task_id = resp.json['content']['task-id']
        expected = 'asdf-asdf-asdf'

        self.assertEqual(task_id, expected)

    def test_post_task(self):
        """GatewayView - POST on /api/1/inf/gateway returns a task-id"""
        resp = self.app.post('/api/1/inf/gateway',
                             headers={'X-Auth': self.token},
                             json={'wan': "someWAN", 'lan': "someLAN"})

        task_id = resp.json['content']['task-id']
        expected = 'asdf-asdf-asdf'

        self.assertEqual(task_id, expected)

    def test_delete_task(self):
        """GatewayView - DELETE on /api/1/inf/gateway returns a task-id"""
        resp = self.app.delete('/api/1/inf/gateway',
                             headers={'X-Auth': self.token})

        task_id = resp.json['content']['task-id']
        expected = 'asdf-asdf-asdf'

        self.assertEqual(task_id, expected)


if __name__ == '__main__':
    unittest.main()
