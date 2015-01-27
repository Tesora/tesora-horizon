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

import copy
import logging

from django.core.urlresolvers import reverse
from django import http
from mox import IsA  # noqa

from openstack_dashboard import api
from openstack_dashboard.dashboards.project.database_configurations \
    import config_param_manager
from openstack_dashboard.test import helpers as test


INDEX_URL = reverse('horizon:project:database_configurations:index')
CREATE_URL = reverse('horizon:project:database_configurations:create')
DETAIL_URL = 'horizon:project:database_configurations:detail'
ADD_URL = 'horizon:project:database_configurations:add'


class DatabaseConfigurationsTests(test.TestCase):
    @test.create_stubs({api.trove: ('configuration_list',)})
    def test_index(self):
        api.trove.configuration_list(IsA(http.HttpRequest)) \
            .AndReturn(self.database_configurations.list())
        self.mox.ReplayAll()
        res = self.client.get(INDEX_URL)
        self.assertTemplateUsed(res,
                                'project/database_configurations/index.html')

    @test.create_stubs({api.trove: ('configuration_list',)})
    def test_index_exception(self):
        api.trove.configuration_list(IsA(http.HttpRequest)) \
            .AndRaise(self.exceptions.trove)
        self.mox.ReplayAll()
        res = self.client.get(INDEX_URL)
        self.assertTemplateUsed(
            res, 'project/database_configurations/index.html')
        self.assertEqual(res.status_code, 200)
        self.assertMessageCount(res, error=1)

    @test.create_stubs({
        api.trove: ('datastore_list', 'datastore_version_list')})
    def test_create_configuration(self):
        api.trove.datastore_list(IsA(http.HttpRequest)) \
            .AndReturn(self.datastores.list())
        api.trove.datastore_version_list(IsA(http.HttpRequest), IsA(str)) \
            .AndReturn(self.datastore_versions.list())
        self.mox.ReplayAll()
        res = self.client.get(CREATE_URL)
        self.assertTemplateUsed(res,
                                'project/database_configurations/create.html')

    @test.create_stubs({api.trove: ('datastore_list',)})
    def test_create_configuration_exception_on_datastore(self):
        api.trove.datastore_list(IsA(http.HttpRequest)) \
            .AndRaise(self.exceptions.trove)
        self.mox.ReplayAll()
        toSuppress = ["openstack_dashboard.dashboards.project."
                      "database_configurations.forms", ]

        # Suppress expected log messages in the test output
        loggers = []
        for cls in toSuppress:
            logger = logging.getLogger(cls)
            loggers.append((logger, logger.getEffectiveLevel()))
            logger.setLevel(logging.CRITICAL)

        try:
            res = self.client.get(CREATE_URL)
            self.assertEqual(res.status_code, 302)

        finally:
            # Restore the previous log levels
            for (log, level) in loggers:
                log.setLevel(level)

    @test.create_stubs({
        api.trove: ('datastore_list', 'datastore_version_list',
                    'configuration_create')})
    def _test_create_test_configuration(
            self, config_description=u''):
        api.trove.datastore_list(IsA(http.HttpRequest)) \
            .AndReturn(self.datastores.list())
        api.trove.datastore_version_list(IsA(http.HttpRequest), IsA(str)) \
            .AndReturn(self.datastore_versions.list())

        name = u'config1'
        values = "{}"
        config_datastore = self.datastores.first().name
        config_datastore_version = self.datastore_versions.first().name

        api.trove.configuration_create(
            IsA(http.HttpRequest),
            name,
            values,
            description=config_description,
            datastore=config_datastore,
            datastore_version=config_datastore_version) \
            .AndReturn(self.database_configurations.first())

        self.mox.ReplayAll()
        post = {
            'method': 'CreateConfigurationForm',
            'name': name,
            'description': config_description,
            'datastore': (config_datastore + ',' + config_datastore_version)}

        res = self.client.post(CREATE_URL, post)
        self.assertNoFormErrors(res)
        self.assertMessageCount(success=1)

    def test_create_test_configuration(self):
        self._test_create_test_configuration(u'description of config1')

    def test_create_test_configuration_with_no_description(self):
        self._test_create_test_configuration()

    @test.create_stubs({
        api.trove: ('datastore_list', 'datastore_version_list',
                    'configuration_create')})
    def test_create_test_configuration_exception(self):
        api.trove.datastore_list(IsA(http.HttpRequest)) \
            .AndReturn(self.datastores.list())
        api.trove.datastore_version_list(IsA(http.HttpRequest), IsA(str)) \
            .AndReturn(self.datastore_versions.list())

        name = u'config1'
        values = "{}"
        config_description = u'description of config1'
        config_datastore = self.datastores.first().name
        config_datastore_version = self.datastore_versions.first().name

        api.trove.configuration_create(
            IsA(http.HttpRequest),
            name,
            values,
            description=config_description,
            datastore=config_datastore,
            datastore_version=config_datastore_version) \
            .AndRaise(self.exceptions.trove)

        self.mox.ReplayAll()
        post = {'method': 'CreateConfigurationForm',
                'name': name,
                'description': config_description,
                'datastore': config_datastore + ',' + config_datastore_version}

        res = self.client.post(CREATE_URL, post)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.trove: ('configuration_get',)})
    def test_details_tab(self):
        config = self.database_configurations.first()
        api.trove.configuration_get(IsA(http.HttpRequest),
                                    config.id) \
            .AndReturn(config)
        self.mox.ReplayAll()
        details_url = self._get_url_with_arg(DETAIL_URL, config.id)
        url = details_url + '?tab=configuration_details__details'
        res = self.client.get(url)
        self.assertTemplateUsed(res,
                                'project/database_configurations/details.html')

    @test.create_stubs({api.trove: ('configuration_get',)})
    def test_overview_tab_exception(self):
        config = self.database_configurations.first()
        api.trove.configuration_get(IsA(http.HttpRequest),
                                    IsA(unicode)) \
            .AndRaise(self.exceptions.trove)
        self.mox.ReplayAll()
        details_url = self._get_url_with_arg(DETAIL_URL, config.id)
        url = details_url + '?tab=configuration_details__overview'
        res = self.client.get(url)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({
        api.trove: ('configuration_get', 'configuration_parameters_list',),
        config_param_manager.ConfigParamManager:
            ('get_configuration', 'configuration_get',)})
    def test_add_parameter(self):
        config = config_param_manager.ConfigParamManager.get_configuration() \
            .AndReturn(self.database_configurations.first())

        config_param_manager.ConfigParamManager \
            .configuration_get(IsA(http.HttpRequest)) \
            .AndReturn(config)

        api.trove.configuration_parameters_list(
            IsA(http.HttpRequest),
            self.datastores.first().name,
            self.datastore_versions.first().name) \
            .AndReturn(self.configuration_parameters.list())
        self.mox.ReplayAll()
        res = self.client.get(self._get_url_with_arg(ADD_URL, 'id'))
        self.assertTemplateUsed(
            res, 'project/database_configurations/add_parameter.html')

    @test.create_stubs({
        api.trove: ('configuration_get', 'configuration_parameters_list',),
        config_param_manager.ConfigParamManager:
            ('get_configuration', 'configuration_get',)})
    def test_add_parameter_exception_on_parameters(self):
        try:
            config = (config_param_manager.ConfigParamManager
                      .get_configuration()
                      .AndReturn(self.database_configurations.first()))

            config_param_manager.ConfigParamManager \
                .configuration_get(IsA(http.HttpRequest)) \
                .AndReturn(config)

            api.trove.configuration_parameters_list(
                IsA(http.HttpRequest),
                self.datastores.first().name,
                self.datastore_versions.first().name) \
                .AndRaise(self.exceptions.trove)
            self.mox.ReplayAll()
            toSuppress = ["openstack_dashboard.dashboards.project."
                          "database_configurations.forms", ]

            # Suppress expected log messages in the test output
            loggers = []
            for cls in toSuppress:
                logger = logging.getLogger(cls)
                loggers.append((logger, logger.getEffectiveLevel()))
                logger.setLevel(logging.CRITICAL)

            try:
                res = self.client.get(
                    self._get_url_with_arg(ADD_URL, config.id))
                self.assertEqual(res.status_code, 302)

            finally:
                # Restore the previous log levels
                for (log, level) in loggers:
                    log.setLevel(level)
        finally:
            config_param_manager.delete(config.id)

    @test.create_stubs({
        api.trove: ('configuration_get', 'configuration_parameters_list',),
        config_param_manager.ConfigParamManager:
            ('get_configuration', 'add_param', 'configuration_get',)})
    def test_add_new_parameter(self):
        try:
            config = (config_param_manager.ConfigParamManager
                      .get_configuration()
                      .AndReturn(self.database_configurations.first()))

            config_param_manager.ConfigParamManager \
                .configuration_get(IsA(http.HttpRequest)) \
                .AndReturn(config)

            api.trove.configuration_parameters_list(
                IsA(http.HttpRequest),
                self.datastores.first().name,
                self.datastore_versions.first().name) \
                .AndReturn(self.configuration_parameters.list())

            name = self.configuration_parameters.first().name
            value = 1

            config_param_manager.ConfigParamManager.add_param(name, value) \
                .AndReturn(value)

            self.mox.ReplayAll()
            post = {
                'method': 'AddParameterForm',
                'name': name,
                'value': value}

            res = self.client.post(self._get_url_with_arg(ADD_URL, config.id),
                                   post)
            self.assertNoFormErrors(res)
            self.assertMessageCount(success=1)
        finally:
            config_param_manager.delete(config.id)

    @test.create_stubs({
        api.trove: ('configuration_get', 'configuration_parameters_list',),
        config_param_manager: ('get',)})
    def test_add_parameter_invalid_value(self):
        try:
            config = self.database_configurations.first()

            # setup the configuration parameter manager
            config_param_mgr = config_param_manager.ConfigParamManager(
                config.id)
            config_param_mgr.configuration = config
            config_param_mgr.original_configuration_values = \
                dict.copy(config.values)

            config_param_manager.get(IsA(http.HttpRequest), config.id) \
                .MultipleTimes().AndReturn(config_param_mgr)

            api.trove.configuration_parameters_list(
                IsA(http.HttpRequest),
                self.datastores.first().name,
                self.datastore_versions.first().name) \
                .AndReturn(self.configuration_parameters.list())

            name = self.configuration_parameters.first().name
            value = "non-numeric"

            self.mox.ReplayAll()
            post = {
                'method': 'AddParameterForm',
                'name': name,
                'value': value}

            res = self.client.post(self._get_url_with_arg(ADD_URL, config.id),
                                   post)
            self.assertFormError(res, "form", 'value',
                                 ['Value must be a number between 0 and 1'])
        finally:
            config_param_manager.delete(config.id)

    # @test.create_stubs({config_param_manager: ('get',)})
    @test.create_stubs({api.trove: ('configuration_get',)})
    def test_values_tab_discard_action(self):
        config = self.database_configurations.first()

        api.trove.configuration_get(IsA(http.HttpRequest), config.id) \
            .MultipleTimes().AndReturn(config)
        self.mox.ReplayAll()

        details_url = self._get_url_with_arg(DETAIL_URL, config.id)
        url = details_url + '?tab=configuration_details__value'

        self._test_create_altered_config_params(config, url)

        # get the state of the configuration before discard action
        changed_configuration_values = \
            dict.copy(config_param_manager.get(self.request, config.id)
                      .get_configuration().values)

        res = self.client.post(url, {'action': u"values__discard_changes"})
        self.assertRedirectsNoFollow(res, url)

        # get the state of the configuration after discard action
        restored_configuration_values = \
            dict.copy(config_param_manager.get(self.request, config.id)
                      .get_configuration().values)

        self.assertTrue(config_param_manager.dict_has_changes(
            changed_configuration_values, restored_configuration_values))

    @test.create_stubs({api.trove: ('configuration_update',),
                        config_param_manager: ('get',)})
    def test_values_tab_apply_action(self):
        config = copy.deepcopy(self.database_configurations.first())

        # setup the configuration parameter manager
        config_param_mgr = config_param_manager.ConfigParamManager(
            config.id)
        config_param_mgr.configuration = config
        config_param_mgr.original_configuration_values = \
            dict.copy(config.values)

        config_param_manager.get(IsA(http.HttpRequest), config.id) \
            .MultipleTimes().AndReturn(config_param_mgr)

        api.trove.configuration_update(
            IsA(http.HttpRequest),
            config.id,
            config_param_mgr.to_json()) \
            .AndReturn(None)
        self.mox.ReplayAll()

        details_url = self._get_url_with_arg(DETAIL_URL, config.id)
        url = details_url + '?tab=configuration_details__value'

        self._test_create_altered_config_params(config, url)

        # apply changes
        res = self.client.post(url, {'action': u"values__apply_changes"})
        self.assertRedirectsNoFollow(res, url)

    @test.create_stubs({api.trove: ('configuration_update',),
                        config_param_manager: ('get',)})
    def test_values_tab_apply_action_exception(self):
        config = copy.deepcopy(self.database_configurations.first())

        # setup the configuration parameter manager
        config_param_mgr = config_param_manager.ConfigParamManager(
            config.id)
        config_param_mgr.configuration = config
        config_param_mgr.original_configuration_values = \
            dict.copy(config.values)

        config_param_manager.get(IsA(http.HttpRequest), config.id) \
            .MultipleTimes().AndReturn(config_param_mgr)

        api.trove.configuration_update(
            IsA(http.HttpRequest),
            config.id,
            config_param_mgr.to_json())\
            .AndRaise(self.exceptions.trove)
        self.mox.ReplayAll()

        details_url = self._get_url_with_arg(DETAIL_URL, config.id)
        url = details_url + '?tab=configuration_details__value'

        self._test_create_altered_config_params(config, url)

        # apply changes
        res = self.client.post(url, {'action': u"values__apply_changes"})
        self.assertRedirectsNoFollow(res, url)
        self.assertEqual(res.status_code, 302)

    def _test_create_altered_config_params(self, config, url):
        # setup the configuration parameter manager
        # config_param_mgr = config_param_manager.get(self.request, config.id)
        # config_param_mgr.configuration = config
        # config_param_mgr.original_configuration_values = \
        #     dict.copy(config.values)

        # determine the number of configuration group parameters in the list
        res = self.client.get(url)

        table_data = res.context['table'].data
        number_params = len(table_data)
        config_param = table_data[0]

        # delete the first parameter
        action_string = u"values__delete__%s" % config_param.name
        form_data = {'action': action_string}
        res = self.client.post(url, form_data)
        self.assertRedirectsNoFollow(res, url)

        # verify the test number of parameters is reduced by 1
        res = self.client.get(url)
        table_data = res.context['table'].data
        new_number_params = len(table_data)

        self.assertEqual((number_params - 1), new_number_params)

    @test.create_stubs({api.trove: ('configuration_instances',),
                        config_param_manager: ('get',)})
    def test_instances_tab(self):
        try:
            config = self.database_configurations.first()

            # setup the configuration parameter manager
            config_param_mgr = config_param_manager.ConfigParamManager(
                config.id)
            config_param_mgr.configuration = config
            config_param_mgr.original_configuration_values = \
                dict.copy(config.values)

            config_param_manager.get(IsA(http.HttpRequest), config.id) \
                .MultipleTimes().AndReturn(config_param_mgr)

            api.trove.configuration_instances(IsA(http.HttpRequest),
                                              config.id)\
                .AndReturn(self.configuration_instances.list())
            self.mox.ReplayAll()

            details_url = self._get_url_with_arg(DETAIL_URL, config.id)
            url = details_url + '?tab=configuration_details__instance'

            res = self.client.get(url)
            table_data = res.context['instances_table'].data
            self.assertItemsEqual(
                self.configuration_instances.list(), table_data)
            self.assertTemplateUsed(
                res, 'project/database_configurations/details.html')
        finally:
            config_param_manager.delete(config.id)

    @test.create_stubs({api.trove: ('configuration_instances',),
                        config_param_manager: ('get',)})
    def test_instances_tab_exception(self):
        try:
            config = self.database_configurations.first()

            # setup the configuration parameter manager
            config_param_mgr = config_param_manager.ConfigParamManager(
                config.id)
            config_param_mgr.configuration = config
            config_param_mgr.original_configuration_values = \
                dict.copy(config.values)

            config_param_manager.get(IsA(http.HttpRequest), config.id) \
                .MultipleTimes().AndReturn(config_param_mgr)

            api.trove.configuration_instances(IsA(http.HttpRequest),
                                              config.id) \
                .AndRaise(self.exceptions.trove)
            self.mox.ReplayAll()

            details_url = self._get_url_with_arg(DETAIL_URL, config.id)
            url = details_url + '?tab=configuration_details__instance'

            res = self.client.get(url)
            table_data = res.context['instances_table'].data
            self.assertNotEqual(len(self.configuration_instances.list()),
                                len(table_data))
            self.assertTemplateUsed(
                res, 'project/database_configurations/details.html')
        finally:
            config_param_manager.delete(config.id)

    def _get_url_with_arg(self, url, arg):
        return reverse(url, args=[arg])
