#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
Network gateway RESTful API for vLab
"""
from setuptools import setup, find_packages


setup(name="vlab-gateway-api",
      author="Nicholas Willhite",
      author_email='willnx84@gmail.com',
      version='2018.12.20',
      packages=find_packages(),
      include_package_data=True,
      package_files={'vlab_gatewway_api' : ['app.ini']},
      description="A service for creating a network gateway in vLab",
      long_description=open('README.rst').read(),
      install_requires=['flask', 'pyjwt', 'uwsgi', 'vlab-api-common', 'ujson',
                        'cryptography', 'celery', 'vlab-inf-common']
      )
