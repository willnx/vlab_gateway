# -*- coding: UTF-8 -*-
"""
Defines the HTTP API for working with network gateways in vLab
"""
import ujson
from flask import current_app
from flask_classy import request, route, Response
from jsonschema import validate, ValidationError
from vlab_inf_common.views import TaskView
from vlab_api_common import describe, get_logger, requires, validate_input

from vlab_gateway_api.lib import const

logger = get_logger(__name__, loglevel=const.VLAB_GATEWAY_LOG_LEVEL)


class GatewayView(TaskView):
    """Defines the HTTP API for working with virtual local area networks"""
    route_base = '/api/1/inf/gateway'
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
        resp_data = {'user' : username}
        task = current_app.celery_app.send_task('gateway.show', [username])
        resp_data['content'] = {'task-id': task.id}
        resp = Response(ujson.dumps(resp_data))
        resp.status_code = 202
        resp.headers.add('Link', '<{0}{1}/task/{2}>; rel=status'.format(const.VLAB_URL, self.route_base, task.id))
        return resp

    @requires(verify=False, version=(1,2)) # XXX remove verify=False before commit
    @validate_input(schema=POST_SCHEMA)
    def post(self, *args, **kwargs):
        """Create a new gateway"""
        username = kwargs['token']['username']
        resp_data = {'user' : username}
        wan = kwargs['body']['wan']
        lan = kwargs['body']['lan']
        task = current_app.celery_app.send_task('gateway.create', [username, wan, lan])
        resp_data['content'] = {'task-id': task.id}
        resp = Response(ujson.dumps(resp_data))
        resp.status_code = 202
        resp.headers.add('Link', '<{0}{1}/task/{2}>; rel=status'.format(const.VLAB_URL, self.route_base, task.id))
        return resp

    @requires(verify=False, version=(1,2)) # XXX remove verify=False before commit
    def delete(self, *args, **kwargs):
        """Delete a gateway"""
        username = kwargs['token']['username']
        resp_data = {'user' : username}
        task = current_app.celery_app.send_task('gateway.delete', [username])
        resp_data['content'] = {'task-id': task.id}
        resp = Response(ujson.dumps(resp_data))
        resp.status_code = 202
        resp.headers.add('Link', '<{0}{1}/task/{2}>; rel=status'.format(const.VLAB_URL, self.route_base, task.id))
        return resp
