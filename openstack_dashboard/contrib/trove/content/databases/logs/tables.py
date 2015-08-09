# Copyright 2015 Tesora Inc.
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

from django.core import urlresolvers
from django.template import defaultfilters as filters
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy

from horizon import tables

from openstack_dashboard.contrib.trove import api


class PublishLog(tables.BatchAction):
    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Publish",
            u"Publish All",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Published",
            u"Published All",
            count
        )

    name = "publish_log"

    def allowed(self, request, datum=None):
        if datum:
            return datum.publishable
        return False

    def action(self, request, obj_id):
        instance_id = self.table.kwargs['instance_id']
        api.trove.log_publish(request, instance_id, obj_id)


class DisableLogCollection(tables.BatchAction):
    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Stop Collection",
            u"Stop Collection",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Stopped Collection",
            u"Stopped Collection",
            count
        )

    name = "disable_log_collection"

    def allowed(self, request, datum=None):
        if datum:
            return datum.status
        return False

    def action(self, request, obj_id):
        instance_id = self.table.kwargs['instance_id']
        api.trove.log_publish(request, instance_id, obj_id, disable=True)


class ViewLog(tables.LinkAction):
    name = "view_log"
    verbose_name = _("View Log")
    url = "horizon:project:databases:logs:log_contents"

    def get_link_url(self, datum):
        instance_id = self.table.kwargs['instance_id']
        return urlresolvers.reverse(self.url,
                                    args=(instance_id,
                                          datum.name))


class LogsTable(tables.DataTable):
    name = tables.Column('name', verbose_name=_('Name'))
    type = tables.Column('type', verbose_name=_("Type"))
    status = tables.Column('status', verbose_name=_("Log Collected"),
                           filters=(filters.yesno, filters.capfirst))
    publishable = tables.Column('publishable', verbose_name=_('Can Publish'),
                                filters=(filters.yesno, filters.capfirst))
    container = tables.Column('container', verbose_name=_('Container'))

    class Meta(object):
        name = "logs"
        verbose_name = _("Logs")
        row_actions = (ViewLog, PublishLog, DisableLogCollection)

    def get_object_id(self, datum):
        return datum.name
