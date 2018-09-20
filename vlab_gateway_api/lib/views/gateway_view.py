# -*- coding: UTF-8 -*-
"""
Defines the HTTP API for working with network gateways in vLab
"""
import ujson
from flask import current_app
from flask_classy import request, route
from jsonschema import validate, ValidationError
from vlab_inf_common.views import TaskView
from vlab_api_common import describe, get_logger, requires, validate_input

from vlab_gateway_api.lib import const

logger = get_logger(__name__, loglevel=const.VLAB_GATEWAY_LOG_LEVEL)


class GatewayView(TaskView):
    """Defines the HTTP API for working with virtual local area networks"""
    route_base = 'api/1/inf/gateway'
    POST_SCHEMA = { "$schema": "http://json-schema.org/draft-04/schema#",
                    "type": "object",
                    "properties": {
                        "wan": {
                            "description": "The name of the Wide Area Network to connect to",
                            "type": "string"
                        },
                        "lan": {
                            "description": "The name of the Local Area Network to connect to",
                            "type": "string"
                        }
                    },
                    "required":[
                        "wan",
                        "lan"
                    ]
                  }

    @requires(verify=False, version=(1,2))
    @describe(post=POST_SCHEMA, delete={}, get_args={})
    def get(self, *args, **kwargs):
        """Obtain a info about the gateways a user owns"""
        username = kwargs['token']['username']
        resp = {'user' : username}
        task = current_app.celery_app.send_task('gateway.show', [username])
        resp['content'] = {'task-id': task.id}
        return ujson.dumps(resp), 200

    @requires(verify=False, version=(1,2)) # XXX remove verify=False before commit
    @validate_input(schema=POST_SCHEMA)
    def post(self, *args, **kwargs):
        """Create a new gateway"""
        username = kwargs['token']['username']
        resp = {'user' : username}
        wan = kwargs['body']['wan']
        lan = kwargs['body']['lan']
        task = current_app.celery_app.send_task('gateway.create', [username, wan, lan])
        resp['content'] = {'task-id': task.id}
        return ujson.dumps(resp), 200

    @requires(verify=False, version=(1,2)) # XXX remove verify=False before commit
    def delete(self, *args, **kwargs):
        """Delete a gateway"""
        username = kwargs['token']['username']
        resp = {'user' : username}
        task = current_app.celery_app.send_task('gateway.delete', [username])
        resp['content'] = {'task-id': task.id}
        return ujson.dumps(resp), 200
