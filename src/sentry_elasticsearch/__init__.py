# -*- coding: utf-8 -*-

try:
    VERSION = __import__('pkg_resources') \
        .get_distribution('sentry-elasticsearch').version
except Exception, e:
    VERSION = 'unknown'
