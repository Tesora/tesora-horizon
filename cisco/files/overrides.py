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

import horizon


try:
    projects_dashboard = horizon.get_dashboard("project")

    projects_dashboard.panels = tuple(
        [panels for panels in projects_dashboard.panels
         if panels.slug != 'database'])

    projects_dashboard._panel_groups = {
        key: value
        for key, value in projects_dashboard._panel_groups.iteritems()
        if value.slug != 'database'
    }

    mydict = {}
    for key, value in projects_dashboard._registry.iteritems():
        if value.slug in ('databases', 'database_backups', 'database_clusters',
                          'database_datastores', 'database_configurations'):
            module = value.__module__
            if module.startswith('openstack_dashboard'):
                continue
        mydict[key] = value
    projects_dashboard._registry = mydict
except Exception:
    pass
