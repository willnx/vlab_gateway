# -*- coding: UTF-8 -*-
"""
Enables Health checks for the Links service
"""
from time import time
import pkg_resources

import ujson
from flask_classy import FlaskView


class HealthView(FlaskView):
    """Logic for checking service health"""
    route_base = '/api/1/inf/gateway/healthcheck'
    trailing_slash = False

    def get(self):
        """API end point for checking service health"""
        stime = time()
        version = pkg_resources.get_distribution('vlab-gateway-api').version
        return ujson.dumps({'latency' : time() - stime, 'version' : version}), 200
