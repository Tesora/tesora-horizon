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

from django.core import urlresolvers
from django.template import defaultfilters as filters
from django.utils.translation import ugettext_lazy as _

from horizon import tables


def get_version_name(datastore):
    try:
        version_id = datastore.default_version
    except AttributeError:
        pass
    else:
        for version in datastore.versions:
            if version['id'] == version_id:
                return version['name']
    return _("Not available")


class DatastoresTable(tables.DataTable):
    name = tables.Column("name",
                         link="horizon:project:database_datastores:detail",
                         verbose_name=_("Datastore Name"))
    id = tables.Column("id", verbose_name="Datastore ID")
    version = tables.Column(get_version_name,
                            verbose_name=_("Default Version"))

    class Meta(object):
        name = "datastores"
        verbose_name = _("Datastores")


def get_image_url(version):
    return urlresolvers.reverse("horizon:project:images:images:detail",
                                args=[version.image])


class VersionsTable(tables.DataTable):
    name = tables.Column("name", verbose_name=_("Version name"))
    id = tables.Column("id", verbose_name=_("Version ID"))
    active = tables.Column("active", verbose_name=_("Active"),
                           filters=(filters.yesno, filters.capfirst),
                           permissions=['openstack.roles.admin'])
    packages = tables.Column("packages", verbose_name=_("Packages"),
                             permissions=['openstack.roles.admin'])
    image = tables.Column("image",
                          link=get_image_url,
                          verbose_name=_("Image ID"),
                          permissions=['openstack.roles.admin'])

    class Meta(object):
        name = "versions"
        verbose_name = _("Versions")
