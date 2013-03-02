# -*- coding: utf-8 -*-
"""
sentry_elasticsearch.plugin
~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module performs elasticsearch indexing of Sentry event tags, which
are compressed as GZipDictField and, for this reason, slow to perform
searches on.

This plugin allows to retrieve event IDs (not groups!) from generic
queries on tag fields.

:copyright: (c) 2013 Federico Maggi
:license: BSD
"""
import sys
import logging

from django import forms

from sentry.plugins import Plugin
from sentry.utils.safe import safe_execute
from django.utils.translation import ugettext_lazy as _

import sentry_elasticsearch

from pyes import ES

logger = logging.getLogger('sentry.plugins.elasticsearch')

PYES_DOC = '<a href="http://pyes.readthedocs.org/">the PyES doc</a>'

class ElasticSearchOptionsForm(forms.Form):
    #TODO: validate
    es_conn_string = forms.CharField(
        label=_('ElasticSearch Connection String'),
        initial='127.0.0.1:9500',
        help_text=_('(e.g., localhost:9500). See %s for valid '\
                        'connection strings and port options' % PYES_DOC))

    es_index_name = forms.CharField(
        label=_('ElasticSearch Index Name'),
        required=False,
        help_text='If left blank, the index will'\
            'be sentry-&lt;project_slug&gt;')


class ElasticSearchPlugin(Plugin):
    title = _('ElasticSearch')
    slug = 'elasticsearch'
    description = _('ElastiSearch indexing of Sentry event tags')
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
        logger.debug('New instance of ElasticSearchPlugin created')
        self.es_conn = None
        self.es_index = None
        self.is_setup = False

    def is_configured(self, project, **kwargs):
        return all(self.get_option(k, project) for k in (
                'es_conn_string',
                'es_index_name'))

    def set_index(self, project):
        logger.debug('Setting up the index')
        if self.es_index is None:
           _es_index = self.get_option('es_index_name', project)
           if not isinstance(_es_index, basestring):
               self.es_index = self.ES_INDEX_NAME_TEMPLATE % {
                   'project_name': project.slug }
           else:
               self.es_index = _es_index
           logger.debug('Index is now %s', self.es_index)

    def set_connection(self, project):
        logger.debug('Setting up connection')
        if self.es_conn is None:
            try:
                cs = self.get_option('es_conn_string', project)
                logger.debug('Creating connection to %s', cs)
                self.es_conn = ES(cs)
            except Exception, e:
                logger.warning('Error setting up the connection: %s', e)
                return
        logger.debug('Connection created successfully')
        if not self.es_conn.exists_index(self.es_index):
            logger.debug('Creating index "%s"', self.es_index)
            try:
                self.es_conn.create_index(self.es_index)
            except Exception, e:
                logger.warning('Error creating the index "%s": %s',\
                                   self.es_index, e)

    def setup(self, project):
        logger.debug('Setting up plugin for project "%s"', project.slug)
        self.set_index(project)
        self.set_connection(project)
        self.is_setup = True

    def post_process(self, group, event, is_new, is_sample, **kwargs):
        logger.debug('Post processing event %s, group %s', event, group)
        configured = self.is_configured(group.project)
        if not configured or not is_new:
            logger.debug('Returning: is_new? %s, configured? %s', \
                             configured, is_new)
            return

        logger.debug('Working on event %s, group %s', event, group)

        if not self.is_setup:
            logger.debug('Setupping on event %s', event)
            self.setup(group.project)

        self.index(event)

    def index(self, event):
        logger.debug('Indexing event %s', event)

        if self.es_conn is None:
            logger.warning('No connection to ElasticSearch server %s', \
                               self.es_conn_string)
            return

        data = None
        try:
            data = event.data.get('extra', None)
        except Exception, e:
            logger.warning('Could not retrieve extra data: %s', e)

        if data is not None:
            data.update({'id': event.id})

            logger.debug('Indexing JSON %s', str(data.keys()))

            try:
                self.es_conn.index(data)
            except Exception, e:
                logger.warning('Error indexing event: %s', e)
