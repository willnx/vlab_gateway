# -*- coding: UTF-8 -*-
"""
Entry point logic for available backend worker tasks
"""
from celery import Celery
from vlab_api_common import get_task_logger

from vlab_gateway_api.lib import const
from vlab_gateway_api.lib.worker import vmware


app = Celery('gateway', backend='rpc://', broker=const.VLAB_MESSAGE_BROKER)


@app.task(name='gateway.show', bind=True)
def show(self, username, txn_id):
    """Obtain basic information about a user's default gateway

    :Returns: Dictionary

    :param username: The name of the user who wants info about their default gateway
    :type username: String
    """
    logger = get_task_logger(txn_id=txn_id, task_id=self.request.id, loglevel=const.VLAB_GATEWAY_LOG_LEVEL.upper())
    resp = {'content' : {}, 'error': None, 'params': {}}
    try:
        logger.info('Task starting')
        info = vmware.show_gateway(username)
    except ValueError as doh:
        logger.error('Task failed: {}'.format(doh))
        resp['error'] = '{}'.format(doh)
    else:
        logger.info('Task complete')
        resp['content'] = info
    return resp


@app.task(name='gateway.create', bind=True)
def create(self, username, wan, lan, txn_id):
    """Deploy a new default gateway

    :Returns: Dictionary

    :param username: The name of the user who wants to create a new default gateway
    :type username: String

    :param network: The name of the network that the jumpbox connects to.
    :type network: String
    """
    logger = get_task_logger(txn_id=txn_id, task_id=self.request.id, loglevel=const.VLAB_GATEWAY_LOG_LEVEL.upper())
    resp = {'content' : {}, 'error': None, 'params': {}}
    try:
        logger.info('Task starting')
        resp['content'] = vmware.create_gateway(username, wan, lan)
    except ValueError as doh:
        logger.error('Task failed: {}'.format(doh))
        resp['error'] = '{}'.format(doh)
    logger.info('Task complete')
    return resp


@app.task(name='gateway.delete', bind=True)
def delete(self, username, txn_id):
    """Destroy the default gateway

    :Returns: Dictionary

    :param username: The name of the user who wants to create a new default gateway
    :type username: String
    """
    logger = get_task_logger(txn_id=txn_id, task_id=self.request.id, loglevel=const.VLAB_GATEWAY_LOG_LEVEL.upper())
    resp = {'content' : {}, 'error': None, 'params': {}}
    try:
        logger.info('Task starting')
        info = vmware.delete_gateway(username)
    except ValueError as doh:
        logger.error('Task failed: {}'.format(doh))
        resp['error'] = '{}'.format(doh)
    else:
        logger.info('Task complete')
        resp['content'] = info
    return resp
