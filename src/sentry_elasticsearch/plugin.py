# -*- coding: utf-8 -*-
"""
sentry_elasticsearch.plugin
~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module performs elastisearch indexing of Sentry event tags, which
are compressed as GZipDictField and, for this reason, slow to perform
searches on.

This plugin allows to retrieve event IDs (not groups!) from generic
queries on tag fields.

:copyright: (c) 2013 Federico Maggi
:license: BSD
"""
from django import forms

from sentry.plugins import Plugin
from sentry.utils.safe import safe_execute

from pyes import ES

import sentry_elasticsearch

class ElasticSearchOptionsForm(forms.Form):
    #TODO: validate
    es_conn_string = forms.CharField(
        initial='127.0.0.1:9500',
        help_text='ElasticSearch connection string '\
            '(e.g., localhost:9500).')

    es_index_name = forms.CharField(
        required=False,
        help_text='ElasticSearch index name. If left blank, the index will'\
            'be sentry-<project_slug>')


class ElasticSearch(Plugin):
    title = 'ElasticSearch'
    slug = 'elasticsearch'
    description = 'ElastiSearch indexing of Sentry event tags'
    version = sentry_elasticsearch.VERSION

    author = 'Federico Maggi'
    author_url = 'https://github.com/phretor'

    resource_links = [
        ('Bug Tracker',
         'https://github.com/phretor/sentry-elasticsearch/issues'),
        ('Source',
         'https://github.com/phretor/sentry-elasticsearch'),
        ]

    project_conf_form = ElasticSearchOptionsForm

    ES_INDEX_NAME_TEMPLATE = 'sentry-%(project_name)s'

    def __init__(self):
        es_conn = None
        es_index = None
        is_setup = False

        self.setup(group.project)

    def setup(self, project):
        self.set_index(project)
        self.set_connection(project)
        self.is_setup = True

    def is_configured(self, project, **kwargs):
        return all(self.get_option(k, project) for k in (
                'es_conn_string',
                'es_index_name'))

    def post_process(self, group, event, is_new, is_sample, **kwargs):
        if not is_new or not self.is_configured(group.project):
            return

        if not self.is_setup:
            self.setup(group.project)

        self.index(event)

    def index(self, event):
        if self.es_conn is None:
            return

        data = None
        try:
            data = event.data.get('extra', None)
        except Exception, e:
            pass

        if data is not None:
            data.update({'id': event.id})

            try:
                self.es_conn.index(data)
            except Exception, e:
                pass

    def set_index(self, project):
        if self.es_index is None:
            _es_index = None
            try:
                _es_index = self.get_option('es_index_name', project.slug)
            except Exception, e:
                pass

            if isinstance(_es_index, basestring):
                self.es_index = _es_index
            else:
                self.es_index = self.ES_INDEX_NAME_TEMPLATE % {
                    'project_name': project.slug }

    def set_connection(self, project):
        if self.es_conn is None:
            try:
                self.es_conn = ES(self.get_option('es_conn_string'), project)
            except Exception, e:
                return
        if not self.es_conn.exists_index(self.es_index):
            try:
                self.es_conn.create_index(self.es_index)
            except Exception, e:
                pass
