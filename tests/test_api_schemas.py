# -*- coding: UTF-8 -*-
"""
A suite of tests for the HTTP API schemas
"""
import unittest

from jsonschema import Draft4Validator, validate, ValidationError
from vlab_gateway_api.lib.views import gateway_view


class TestGatwayViewSchema(unittest.TestCase):
    """A set of test cases for the schemas of /api/1/inf/gateway"""

    def test_post_schema(self):
        """The schema defined for POST on is valid"""
        try:
            Draft4Validator.check_schema(gateway_view.GatewayView.POST_SCHEMA)
            schema_valid = True
        except RuntimeError:
            schema_valid = False

        self.assertTrue(schema_valid)

    def test_post_requires_lan(self):
        """The POST schema requires the parameter 'lan'"""
        body = {'wan' : 'someWANnetwork'}
        try:
            validate(body, gateway_view.GatewayView.POST_SCHEMA)
            lan_required = False
        except ValidationError:
            lan_required = True

        self.assertTrue(lan_required)

    def test_post_requires_wan(self):
        """The POST schema requires the parameter 'lan'"""
        body = {'lan' : 'someLANnetwork'}
        try:
            validate(body, gateway_view.GatewayView.POST_SCHEMA)
            wan_required = False
        except ValidationError:
            wan_required = True

        self.assertTrue(wan_required)

    def test_post_no_body(self):
        """The POST schema requires body content to be sent"""
        body = {}
        try:
            validate(body, gateway_view.GatewayView.POST_SCHEMA)
            body_required = False
        except ValidationError:
            body_required = True

        self.assertTrue(body_required)


if __name__ == '__main__':
    unittest.main()
