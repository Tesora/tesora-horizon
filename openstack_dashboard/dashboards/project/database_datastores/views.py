# Copyright 2015 Cloudwatt
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""
Views for listing and managing datastores.
"""
import logging

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tables as horizon_tables
from horizon import tabs as horizon_tabs
from horizon.utils import memoized

from openstack_dashboard import api
from openstack_dashboard.dashboards.project.database_datastores import tables
from openstack_dashboard.dashboards.project.database_datastores import tabs


LOG = logging.getLogger(__name__)


class IndexView(horizon_tables.DataTableView):
    table_class = tables.DatastoresTable
    template_name = 'project/database_datastores/index.html'
    page_title = _("Datastores")

    def get_data(self):
        try:
            datastores = api.trove.datastore_list(self.request)
        except Exception:
            datastores = []
            msg = _('Unable to retrieve datastores list.')
            exceptions.handle(self.request, msg)
        return datastores


class DetailView(horizon_tabs.TabbedTableView):
    tab_group_class = tabs.DatastoreDetailTabs
    template_name = 'project/database_datastores/detail.html'
    page_title = _("Datastore Details: {{ datastore.name }}")

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        table = tables.DatastoresTable(self.request)
        datastore = self.get_data()
        datastore.default_version_name = tables.get_version_name(datastore)
        context["datastore"] = datastore
        context["url"] = self.get_redirect_url()
        context["actions"] = table.render_row_actions(datastore)
        return context

    @memoized.memoized_method
    def get_data(self):
        try:
            datastore_id = self.kwargs['datastore_id']
            LOG.info("Obtaining datastore %s for detailed view", datastore_id)
            datastore = api.trove.datastore_get(self.request, datastore_id)
        except Exception:
            msg = _('Unable to retrieve details '
                    'for datastore: %s') % datastore_id
            exceptions.handle(self.request, msg,
                              redirect=self.get_redirect_url())
        return datastore

    def get_tabs(self, request, *args, **kwargs):
        datastore = self.get_data()
        return self.tab_group_class(request, datastore=datastore, **kwargs)

    @staticmethod
    def get_redirect_url():
        return reverse('horizon:project:database_datastores:index')
