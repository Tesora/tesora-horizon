# Copyright 2016 Tesora Inc.
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

from django.core.urlresolvers import reverse
from django import http

from mox3.mox import IsA  # noqa

from openstack_dashboard.contrib.trove import api
from openstack_dashboard.test import helpers as test


INDEX_URL = reverse('horizon:project:databases:index')


class UpgradeTests(test.TestCase):

    @test.create_stubs(
        {api.trove: ('instance_get', 'datastore_version_list')})
    def test_upgrade_instance_get(self):
        database = self.databases.first()

        api.trove.instance_get(IsA(http.HttpRequest), database.id)\
            .AndReturn(database)
        api.trove.datastore_version_list(IsA(http.HttpRequest),
                                         IsA(str))\
            .AndReturn(self.datastore_versions.list())

        self.mox.ReplayAll()
        url = reverse('horizon:project:databases:upgrade:upgrade_instance',
                      args=[database.id])

        res = self.client.get(url)
        self.assertTemplateUsed(
            res, 'project/databases/upgrade/upgrade_instance.html')

    @test.create_stubs(
        {api.trove: ('instance_get',
                     'datastore_version_list',
                     'instance_upgrade')})
    def test_upgrade_instance(self):
        database = self.databases.first()
        datastore_version = self.datastore_versions.first()

        api.trove.instance_get(IsA(http.HttpRequest), database.id)\
            .AndReturn(database)
        api.trove.datastore_version_list(IsA(http.HttpRequest),
                                         IsA(str))\
            .AndReturn(self.datastore_versions.list())
        api.trove.instance_upgrade(IsA(http.HttpRequest),
                                   database.id,
                                   datastore_version.id).AndReturn(None)

        self.mox.ReplayAll()
        url = reverse('horizon:project:databases:upgrade:upgrade_instance',
                      args=[database.id])
        post = {
            'instance_id': database.id,
            'instance_name': database.name,
            'new_datastore_version': datastore_version.id
        }
        res = self.client.post(url, post)
        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)
