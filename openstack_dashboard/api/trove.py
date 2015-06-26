# Copyright 2013 Rackspace Hosting.
# Copyright 2015 HP Software, LLC
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

import logging

from django.conf import settings
from troveclient.v1 import client

from openstack_dashboard.api import base

from horizon.utils import functions as utils
from horizon.utils.memoized import memoized  # noqa

LOG = logging.getLogger(__name__)


@memoized
def troveclient(request):
    insecure = getattr(settings, 'OPENSTACK_SSL_NO_VERIFY', False)
    cacert = getattr(settings, 'OPENSTACK_SSL_CACERT', None)
    trove_url = base.url_for(request, 'database')
    c = client.Client(request.user.username,
                      request.user.token.id,
                      project_id=request.user.project_id,
                      auth_url=trove_url,
                      insecure=insecure,
                      cacert=cacert,
                      http_log_debug=settings.DEBUG)
    c.client.auth_token = request.user.token.id
    c.client.management_url = trove_url
    return c


def cluster_list(request, marker=None):
    # default_page_size = getattr(settings, 'API_RESULT_PAGE_SIZE', 20)
    # page_size = request.session.get('horizon_pagesize', default_page_size)
    page_size = utils.get_page_size(request)
    return troveclient(request).clusters.list(limit=page_size, marker=marker)


def cluster_get(request, cluster_id):
    return troveclient(request).clusters.get(cluster_id)


def cluster_delete(request, cluster_id):
    return troveclient(request).clusters.delete(cluster_id)


def cluster_create(request, name, volume, flavor, num_instances,
                   datastore, datastore_version, users=None):
    # TODO(dklyle): adding conditional to support trove without volume
    # support for now until API supports checking for volume support
    if volume > 0:
        volume_params = {'size': volume}
    else:
        volume_params = None
    instances = []
    for i in range(0, num_instances):
        instance = {}
        instance["flavorRef"] = flavor
        instance["volume"] = volume_params
        instances.append(instance)

    # It appears the code below depends on this trove change
    # https://review.openstack.org/#/c/166954/.  Comment out when that
    # change merges.
    # return troveclient(request).clusters.create(
    #     name,
    #     datastore,
    #     datastore_version,
    #     instances=instances,
    #     users=users)
    return troveclient(request).clusters.create(
        name,
        datastore,
        datastore_version,
        instances=instances)


def cluster_add_shard(request, cluster_id):
    return troveclient(request).clusters.add_shard(cluster_id)


def cluster_edit_admin(request, cluster_id, user, password):
    # It appears the code below depends on this trove change
    # https://review.openstack.org/#/c/166954/.  Comment out when that
    # change merges.
    # return troveclient(request).cluster.reset_root_password(cluster_id)
    pass


def instance_list(request, marker=None):
    page_size = utils.get_page_size(request)
    return troveclient(request).instances.list(limit=page_size, marker=marker)


def instance_get(request, instance_id):
    return troveclient(request).instances.get(instance_id)


def instance_delete(request, instance_id):
    return troveclient(request).instances.delete(instance_id)


def instance_create(request, name, volume, flavor, databases=None,
                    users=None, restore_point=None, nics=None,
                    datastore=None, datastore_version=None,
                    replica_of=None, configuration=None,
                    replica_count=None):
    # TODO(dklyle): adding conditional to support trove without volume
    # support for now until API supports checking for volume support
    if volume > 0:
        volume_params = {'size': volume}
    else:
        volume_params = None
    return troveclient(request).instances.create(
        name,
        flavor,
        volume=volume_params,
        databases=databases,
        users=users,
        restorePoint=restore_point,
        nics=nics,
        datastore=datastore,
        datastore_version=datastore_version,
        replica_of=replica_of,
        configuration=configuration,
        replica_count=replica_count)


def instance_resize_volume(request, instance_id, size):
    return troveclient(request).instances.resize_volume(instance_id, size)


def instance_resize(request, instance_id, flavor_id):
    return troveclient(request).instances.resize_instance(instance_id,
                                                          flavor_id)


def instance_backups(request, instance_id):
    return troveclient(request).instances.backups(instance_id)


def instance_restart(request, instance_id):
    return troveclient(request).instances.restart(instance_id)


def instance_detach_replica(request, instance_id):
    return troveclient(request).instances.edit(instance_id,
                                               detach_replica_source=True)


def instance_attach_configuration(request, instance_id, configuration):
    return troveclient(request).instances.modify(instance_id,
                                                 configuration=configuration)


def instance_detach_configuration(request, instance_id):
    return troveclient(request).instances.modify(instance_id)


def promote_to_replica_source(request, instance_id):
    return troveclient(request).instances.promote_to_replica_source(
        instance_id)


def eject_replica_source(request, instance_id):
    return troveclient(request).instances.eject_replica_source(instance_id)


def database_list(request, instance_id):
    return troveclient(request).databases.list(instance_id)


def database_create(request, instance_id, db_name, character_set, collation):
    database = {'name': db_name}
    if collation:
        database['collate'] = collation
    if character_set:
        database['character_set'] = character_set
    return troveclient(request).databases.create(instance_id, [database])


def database_delete(request, instance_id, db_name):
    return troveclient(request).databases.delete(instance_id, db_name)


def backup_list(request):
    return troveclient(request).backups.list()


def backup_get(request, backup_id):
    return troveclient(request).backups.get(backup_id)


def backup_delete(request, backup_id):
    return troveclient(request).backups.delete(backup_id)


def backup_create(request, name, instance_id, description=None,
                  parent_id=None):
    return troveclient(request).backups.create(name, instance_id,
                                               description, parent_id)


def flavor_list(request):
    return troveclient(request).flavors.list()


def flavor_get(request, flavor_id):
    return troveclient(request).flavors.get(flavor_id)


def root_enable(request, instance_ids):
    username, password = troveclient(request).root.create(instance_ids[0])
    return username, password


def root_show(request, instance_id):
    return troveclient(request).root.is_root_enabled(instance_id)


def root_disable(request, instance_id):
    return troveclient(request).root.delete(instance_id)


def users_list(request, instance_id):
    return troveclient(request).users.list(instance_id)


def user_create(request, instance_id, username, password, host, databases):
    user = {'name': username, 'password': password}
    if databases:
        user['databases'] = databases
    else:
        user['databases'] = []
    if host:
        user['host'] = host

    return troveclient(request).users.create(instance_id, [user])


def user_delete(request, instance_id, user):
    return troveclient(request).users.delete(instance_id, user)


def user_update_attributes(request, instance_id, name,
                           new_name=None, new_password=None, new_host=None):
    new_attrs = {}
    if new_name:
        new_attrs['name'] = new_name
    if new_password:
        new_attrs['password'] = new_password
    if new_host:
        new_attrs['host'] = new_host
    return troveclient(request).users.update_attributes(
        instance_id, name, new_attrs)


def user_list_access(request, instance_id, user):
    return troveclient(request).users.list_access(instance_id, user)


def user_grant_access(request, instance_id, username, databases, host=None):
    return troveclient(request).users.grant(
        instance_id, username, databases, host)


def user_revoke_access(request, instance_id, username, database, host=None):
    return troveclient(request).users.revoke(
        instance_id, username, database, host)


def user_show_access(request, instance_id, username, host=None):
    return troveclient(request).users.list_access(
        instance_id, username, host)


def datastore_list(request):
    return troveclient(request).datastores.list()


def datastore_version_list(request, datastore_id):
    return troveclient(request).datastore_versions.list(datastore_id)


def datastore_get(request, datastore_id):
    return troveclient(request).datastores.get(datastore_id)


def configuration_list(request):
    return troveclient(request).configurations.list()


def configuration_get(request, group_id):
    return troveclient(request).configurations.get(group_id)


def configuration_parameters_list(request, datastore, datastore_version):
    return troveclient(request).configuration_parameters.\
        parameters(datastore, datastore_version)


def configuration_create(request,
                         name,
                         values,
                         description=None,
                         datastore=None,
                         datastore_version=None):
    return troveclient(request).configurations.create(name,
                                                      values,
                                                      description,
                                                      datastore,
                                                      datastore_version)


def configuration_delete(request, group_id):
    return troveclient(request).configurations.delete(group_id)


def configuration_instances(request, group_id):
    return troveclient(request).configurations.instances(group_id)


def configuration_update(request, group_id, values):
    return troveclient(request).configurations.update(group_id, values)


def configuration_default(request, instance_id):
    return troveclient(request).instances.configuration(instance_id)
