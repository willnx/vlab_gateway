# -*- coding: UTF-8 -*-
"""
A suite of tests for the functions in tasks.py
"""
import unittest
from unittest.mock import patch, MagicMock

from vlab_gateway_api.lib.worker import tasks


class TestTasks(unittest.TestCase):
    """A set of test cases for tasks.py"""

    @patch.object(tasks, 'get_task_logger')
    @patch.object(tasks, 'vmware')
    def test_show_ok(self, fake_vmware, fake_get_task_logger):
        """``show`` returns a dictionary when everything works as expected"""
        fake_vmware.show_gateway.return_value = {'worked': True}

        output = tasks.show(username='bob', txn_id='myId')
        expected = {'content' : {'worked': True}, 'error': None, 'params': {}}

        self.assertEqual(output, expected)

    @patch.object(tasks, 'get_task_logger')
    @patch.object(tasks, 'vmware')
    def test_show_value_error(self, fake_vmware, fake_get_task_logger):
        """``show`` sets the error in the dictionary to the ValueError message"""
        fake_vmware.show_gateway.side_effect = [ValueError("testing")]

        output = tasks.show(username='bob', txn_id='myId')
        expected = {'content' : {}, 'error': 'testing', 'params': {}}

        self.assertEqual(output, expected)

    @patch.object(tasks, 'get_task_logger')
    @patch.object(tasks, 'vmware')
    def test_create_ok(self, fake_vmware, fake_get_task_logger):
        """``create`` returns a dictionary when everything works as expected"""
        fake_vmware.create_gateway.return_value = {'worked': True}

        output = tasks.create(username='bob', wan='SomeWan', lan='someLan', txn_id='myId')
        expected = {'content' : {'worked': True}, 'error': None, 'params': {}}

        self.assertEqual(output, expected)

    @patch.object(tasks, 'get_task_logger')
    @patch.object(tasks, 'vmware')
    def test_create_value_error(self, fake_vmware, fake_get_task_logger):
        """``create`` sets the error in the dictionary to the ValueError message"""
        fake_vmware.create_gateway.side_effect = [ValueError("testing")]

        output = tasks.create(username='bob', wan='SomeWan', lan='someLan', txn_id='myId')
        expected = {'content' : {}, 'error': 'testing', 'params': {}}

        self.assertEqual(output, expected)

    @patch.object(tasks, 'get_task_logger')
    @patch.object(tasks, 'vmware')
    def test_delete_ok(self, fake_vmware, fake_get_task_logger):
        """``delete`` returns a dictionary when everything works as expected"""
        fake_vmware.delete_gateway.return_value = {'worked': True}

        output = tasks.delete(username='bob', txn_id='myId')
        expected = {'content' : {'worked': True}, 'error': None, 'params': {}}

        self.assertEqual(output, expected)

    @patch.object(tasks, 'get_task_logger')
    @patch.object(tasks, 'vmware')
    def test_delete_value_error(self, fake_vmware, fake_get_task_logger):
        """``delete`` sets the error in the dictionary to the ValueError message"""
        fake_vmware.delete_gateway.side_effect = [ValueError("testing")]

        output = tasks.delete(username='bob', txn_id='myId')
        expected = {'content' : {}, 'error': 'testing', 'params': {}}

        self.assertEqual(output, expected)


if __name__ == '__main__':
    unittest.main()
