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

from django import template
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tabs
from openstack_dashboard import api
from openstack_dashboard.dashboards.project.database_datastores import tables


class OverviewTab(tabs.Tab):
    name = _("Overview")
    slug = "overview"

    def get_context_data(self, request):
        return {"datastore": self.tab_group.kwargs['datastore']}

    def get_template_name(self, request):
        template_dir = 'project/database_datastores/%s'
        datastore = self.tab_group.kwargs['datastore']
        template_file = '_detail_overview_%s.html' % datastore.name
        try:
            template.loader.get_template(template_file)
        except template.TemplateDoesNotExist:
            # This datastore type does not have a template file
            # Just use the base template file
            template_file = '_detail_overview.html'
        return template_dir % template_file


class VersionsTab(tabs.TableTab):
    table_classes = [tables.VersionsTable]
    name = _("Versions")
    slug = "versions_tab"
    template_name = "horizon/common/_detail_table.html"

    def get_versions_data(self):
        datastore = self.tab_group.kwargs['datastore']
        try:
            versions = api.trove.datastore_version_list(self.request,
                                                        datastore.id)
        except Exception:
            msg = _('Unable to get versions list.')
            exceptions.handle(self.request, msg)
            versions = []
        return versions


class DatastoreDetailTabs(tabs.TabGroup):
    slug = "datastore_detail"
    tabs = (OverviewTab, VersionsTab)
    sticky = True
