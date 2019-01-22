# -*- coding: UTF-8 -*-
"""
All the things can override via Environment variables are keep in this one file.
"""
from os import environ
from collections import namedtuple, OrderedDict


DEFINED = OrderedDict([
            ('VLAB_URL', environ.get('VLAB_URL', 'https://localhost')),
            ('INF_VCENTER_SERVER', environ.get('INF_VCENTER_SERVER', 'localhost')),
            ('INF_VCENTER_PORT', int(environ.get('INFO_VCENTER_PORT', 443))),
            ('INF_VCENTER_USER', environ.get('INF_VCENTER_USER', 'someAdmin')),
            ('INF_VCENTER_PASSWORD', environ.get('INF_VCENTER_PASSWORD', 'iLoveCats')),
            ('INF_VCENTER_DATASTORE', environ.get('INF_VCENTER_DATASTORE', 'VM-Storage')),
            ('INF_VCENTER_RESORUCE_POOL', environ.get('INF_VCENTER_RESORUCE_POOL', 'Resources')),
            ('VLAB_GATEWAY_LOG_LEVEL', environ.get('VLAB_GATEWAY_LOG_LEVEL', 'INFO')),
            ('VLAB_MESSAGE_BROKER', environ.get('VLAB_MESSAGE_BROKER', 'gateway-broker')),
            ('VLAB_GATEWAY_IMAGES_DIR', environ.get('VLAB_GATEWAY_IMAGES_DIR', '/images')),
            ('INF_VCENTER_TOP_LVL_DIR', environ.get('INF_VCENTER_TOP_LVL_DIR', '/vlab')),
            ('VLAB_DOMAIN', environ.get('VLAB_DOMAIN', 'local')),
            ('VLAB_IPAM_ADMIN', 'administrator'),
            ('VLAB_IPAM_ADMIN_PW', environ.get('VLAB_IPAM_ADMIN_PW', "I'm a little tea pot")),
            ('VLAB_IPAM_KEY', environ.get('VLAB_IPAM_KEY', 'bGfKJfkoAPcvG3dORQuWCBXbGLtl6L9_iSfaKfaLEHY=')),
            ('VLAB_IPAM_BROKER', environ.get('VLAB_IPAM_BROKER', 'localhost:9092')),
            ('VLAB_VERIFY_TOKEN', environ.get('VLAB_VERIFY_TOKEN', False)),
            ('VLAB_DDNS_KEY', environ.get('VLAB_DDNS_KEY', 'aabbcc')),
          ])

Constants = namedtuple('Constants', list(DEFINED.keys()))

# The '*' expands the list, just liked passing a function *args
const = Constants(*list(DEFINED.values()))
