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


MARIA = "maria"
MONGODB = "mongodb"
MYSQL = "mysql"
ORACLE = "oracle"
PERCONA = "percona"
VERTICA = "vertica"

_mysql_compatible_datastores = (MYSQL, MARIA, PERCONA)


def can_backup(datastore):
    if is_oracle_datastore(datastore):
        return False
    return True


def can_launch_from_master(datastore):
    if is_oracle_datastore(datastore):
        return False
    return True


def db_required_when_creating_user(datastore):
    if is_oracle_datastore(datastore):
        return False
    return True


def require_configuration_group(datastore):
    if is_oracle_datastore(datastore):
        return True
    return False


def is_oracle_datastore(datastore):
    return (datastore is not None) and (ORACLE in datastore.lower())


def is_mysql_compatible(datastore):
    if (datastore is not None):
        for ds in _mysql_compatible_datastores:
            if ds in datastore.lower():
                return True
    return False


def is_mongodb_datastore(datastore):
    return (datastore is not None) and (MONGODB in datastore.lower())


def is_vertica_datastore(datastore):
    return (datastore is not None) and (VERTICA in datastore.lower())
