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

from openstack_dashboard import api

from oslo.serialization import jsonutils

_configuration_group_managers = {}


def get(configuration_group_id):
    if not has_config(configuration_group_id):
        _configuration_group_managers[configuration_group_id] = \
            ConfigParamManager(configuration_group_id)

    return _configuration_group_managers[configuration_group_id]


def delete(configuration_group_id):
    del _configuration_group_managers[configuration_group_id]


def has_config(configuration_group_id):
    return configuration_group_id in _configuration_group_managers


class ConfigParamManager(object):

    original_configuration_values = None
    configuration = None

    def __init__(self, configuration_id):
        self.configuration_id = configuration_id

    def configuration_get(self, request):
        if self.configuration is None:
            self.configuration = api.trove.configuration_get(
                request, self.configuration_id)
            self.original_configuration_values = \
                dict.copy(self.configuration.values)
        return self.get_configuration()

    def get_configuration(self):
        return self.configuration

    def create_config_value(self, name, value):
        return ConfigParam(self.configuration_id, name, value)

    def get_param(self, name):
        for key_name in self.configuration.values:
            if key_name == name:
                return self.create_config_value(
                    key_name, self.configuration.values[key_name])
        return None

    def update_param(self, name, value):
        self.configuration.values[name] = value

    def delete_param(self, name):
        del self.configuration.values[name]

    def add_param(self, name, value):
        self.update_param(name, value)

    def to_json(self):
        return jsonutils.dumps(self.configuration.values)

    def has_changes(self):
        if len(self.configuration.values) != \
                len(self.original_configuration_values):
            return True

        diffs = (set(self.original_configuration_values.keys()) -
                 set(self.configuration.values.keys()))
        if len(diffs).__nonzero__():
            return True

        for key in self.original_configuration_values:
            if self.original_configuration_values[key] != \
                    self.configuration.values[key]:
                return True

        return False


class ConfigParam:
    def __init__(self, configuration_id, name, value):
        self.configuration_id = configuration_id
        self.name = name
        self.value = value
