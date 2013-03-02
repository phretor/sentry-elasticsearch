#!/usr/bin/env python
"""
sentry-elasticsearch
====================

This module performs elastisearch indexing of Sentry event tags, which
are compressed as GZipDictField and, for this reason, slow to perform
searches on.

This plugin allows to retrieve event IDs (not groups!) from generic
queries on tag fields.

:copyright: (c) 2013 by Federico Maggi
"""
from setuptools import setup, find_packages

install_requires = [
    'sentry>=5.4.2',
]

setup(
    name='sentry-elastisearch',
    version='0.1.0',
    author='Federico Maggi',
    author_email='federico.maggi@gmail.com',
    url='http://github.com/phretor/sentry-elastisearch',
    description='A Sentry plugin that performs elastisearch indexing.',
    long_description=__doc__,
    license='BSD',
    package_dir={'': 'src'},
    packages=find_packages('src'),
    zip_safe=False,
    install_requires=install_requires,
    tests_require=tests_require,
    extras_require={'test': tests_require},
    include_package_data=True,
    entry_points={
       'sentry.apps': [
            'elasticsearch = sentry_elasticsearch',
        ],
       'sentry.plugins': [
            'elasticsearch = sentry_elasticsearch.plugin:ElasticSearchPlugin'
        ],
    },
    classifiers=[
        'Framework :: Django',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Operating System :: OS Independent',
        'Topic :: Software Development'
    ],
)
