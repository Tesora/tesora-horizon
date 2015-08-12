# Copyright 2015 HP Software, LLC
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import logging

from django.core.urlresolvers import reverse
from django.forms import ValidationError  # noqa
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages
from horizon.utils import memoized

from openstack_dashboard.contrib.trove import api
from openstack_dashboard.contrib.trove.content.databases import db_capability

LOG = logging.getLogger(__name__)


class LaunchForm(forms.SelfHandlingForm):
    name = forms.CharField(label=_("Cluster Name"),
                           max_length=80)
    datastore = forms.ChoiceField(label=_("Datastore"),
                                  help_text=_("Type and version of datastore"),
                                  widget=forms.Select(attrs={
                                      'class': 'switchable',
                                      'data-slug': 'datastore'
                                  }))
    flavor = forms.ChoiceField(label=_("Flavor"),
                               help_text=_("Size of image to launch."),
                               widget=forms.Select(attrs={
                                   'class': 'switched',
                                   'data-switch-on': 'datastore',
                               }))
    vertica_flavor = forms.ChoiceField(label=_("Flavor"),
                                       help_text=_("Size of image to launch."),
                                       required=False,
                                       widget=forms.Select(attrs={
                                           'class': 'switched',
                                           'data-switch-on': 'datastore',
                                       }))
    volume = forms.IntegerField(label=_("Volume Size"),
                                min_value=0,
                                initial=1,
                                help_text=_("Size of the volume in GB."))
    num_instances = forms.IntegerField(label=_("Instances Per Cluster"),
                                       initial=3,
                                       widget=forms.TextInput(
                                           attrs={'readonly': 'readonly'}))
    num_shards = forms.IntegerField(label=_("Number of Shards"),
                                    min_value=1,
                                    initial=1,
                                    required=False,
                                    widget=forms.TextInput(attrs={
                                        'readonly': 'readonly',
                                        'class': 'switched',
                                        'data-switch-on': 'datastore',
                                    }))
    user = forms.CharField(label=_('Initial Admin User'),
                           required=False,
                           help_text=_("Create the admin user that will have "
                                       "access to the cluster"),
                           widget=forms.TextInput(attrs={
                               'class': 'switched',
                               'data-switch-on': 'datastore',
                           }))
    initial_pass = forms.CharField(label=_("Initial Password"),
                                   required=False,
                                   help_text=_(
                                       "Initial password for cluster "
                                       "admin user"),
                                   widget=forms.PasswordInput(attrs={
                                       'class': 'switched',
                                       'data-switch-on': 'datastore',
                                   }))
    control_nodes = forms.IntegerField(label=_("Control Nodes"),
                                       min_value=0,
                                       initial=0,
                                       required=False,
                                       help_text=_(
                                           "For the Beta of Vertica on Helion "
                                           "OpenStack, the topology cannot be "
                                           "changed"),
                                       widget=forms.TextInput(attrs={
                                           'readonly': 'readonly',
                                           'class': 'switched',
                                           'data-switch-on': 'datastore',
                                       }))
    permanent_nodes = forms.IntegerField(label=_("Permanent Nodes"),
                                         min_value=3,
                                         initial=3,
                                         required=False,
                                         help_text=_(
                                             "For the Beta of Vertica on "
                                             "Helion OpenStack, the topology "
                                             "cannot be changed"),
                                         widget=forms.TextInput(attrs={
                                             'readonly': 'readonly',
                                             'class': 'switched',
                                             'data-switch-on': 'datastore',
                                         }))
    standby_nodes = forms.IntegerField(label=_("Standby Nodes"),
                                       min_value=0,
                                       initial=0,
                                       required=False,
                                       help_text=_(
                                           "For the Beta of Vertica on Helion "
                                           "OpenStack, the topology cannot be "
                                           "changed"),
                                       widget=forms.TextInput(attrs={
                                           'readonly': 'readonly',
                                           'class': 'switched',
                                           'data-switch-on': 'datastore',
                                       }))
    # (name of field variable, label)
    mongodb_fields = [
        ('flavor', _('Flavor')),
        ('num_shards', _('Number of Shards')),
    ]
    vertica_fields = [
        ('vertica_flavor', _('Flavor')),
        ('user', _('Initial admin user to enable')),
        ('initial_pass', _('Initial password for cluster access')),
        ('control_nodes', _('Control Nodes')),
        ('permanent_nodes', _('Permanent Nodes')),
        ('standby_nodes', _('Standby Nodes')),
    ]

    def __init__(self, request, *args, **kwargs):
        super(LaunchForm, self).__init__(request, *args, **kwargs)

        self.fields['datastore'].choices = \
            self.populate_datastore_choices(request)
        self.fields['flavor'].choices = \
            self.populate_flavor_choices(request)
        self.fields['vertica_flavor'].choices = \
            self.populate_vertica_flavor_choices(request)

    def clean(self):
        datastore_field_value = self.data.get("datastore", None)
        if datastore_field_value:
            datastore = datastore_field_value.split(',')[0]

            if db_capability.is_mongodb_datastore(datastore):
                if self.data.get("num_shards", None) < 1:
                    msg = _("The number of shards must be greater than 1.")
                    self._errors["num_shards"] = self.error_class([msg])

            elif db_capability.is_vertica_datastore(datastore):
                if not self.data.get("vertica_flavor", None):
                    msg = _("The flavor must be specified.")
                    self._errors["vertica_flavor"] = self.error_class([msg])
                if not self.data.get("user", None):
                    msg = _("The user must be specified.")
                    self._errors["user"] = self.error_class([msg])
                if not self.data.get("initial_pass", None):
                    msg = _("The user password must be specified.")
                    self._errors["initial_pass"] = self.error_class([msg])
                if self.data.get("permanent_nodes", None) < 3:
                    msg = _("Vertica Cluster must maintain at "
                            "least 3 nodes for fault tolerant.")
                    self._errors["permanent_nodes"] = self.error_class([msg])

        return self.cleaned_data

    @memoized.memoized_method
    def flavors(self, request):
        try:
            return api.trove.flavor_list(request)
        except Exception:
            LOG.exception("Exception while obtaining flavors list")
            self._flavors = []
            redirect = reverse('horizon:project:database_clusters:index')
            exceptions.handle(request,
                              _('Unable to obtain flavors.'),
                              redirect=redirect)

    def populate_flavor_choices(self, request):
        flavor_list = [(f.id, "%s" % f.name) for f in self.flavors(request)]
        return sorted(flavor_list)

    def populate_vertica_flavor_choices(self, request):
        valid_flavor = []
        for fl in self.flavors(request):
            if fl.name.lower() == "m1.small":
                valid_flavor.append(fl)
        flavor_list = [(f.id, "%s" % f.name) for f in valid_flavor]
        return sorted(flavor_list)

    @memoized.memoized_method
    def datastores(self, request):
        try:
            return api.trove.datastore_list(request)
        except Exception:
            LOG.exception("Exception while obtaining datastores list")
            self._datastores = []
            redirect = reverse('horizon:project:database_clusters:index')
            exceptions.handle(request,
                              _('Unable to obtain datastores.'),
                              redirect=redirect)

    def filter_cluster_datastores(self, request):
        datastores = []
        for ds in self.datastores(request):
            # TODO(michayu): until capabilities lands
            if db_capability.is_vertica_datastore(ds.name) or \
                    db_capability.is_mongodb_datastore(ds.name):
                datastores.append(ds)
        return datastores

    @memoized.memoized_method
    def datastore_versions(self, request, datastore):
        try:
            return api.trove.datastore_version_list(request, datastore)
        except Exception:
            LOG.exception("Exception while obtaining datastore version list")
            self._datastore_versions = []
            redirect = reverse('horizon:project:database_clusters:index')
            exceptions.handle(request,
                              _('Unable to obtain datastore versions.'),
                              redirect=redirect)

    def populate_datastore_choices(self, request):
        choices = ()
        set_initial = False
        datastores = self.filter_cluster_datastores(request)
        if datastores is not None:
            num_datastores_with_one_version = 0
            for ds in datastores:
                versions = self.datastore_versions(request, ds.name)
                if not set_initial:
                    if len(versions) >= 2:
                        set_initial = True
                    elif len(versions) == 1:
                        num_datastores_with_one_version += 1
                        if num_datastores_with_one_version > 1:
                            set_initial = True
                if len(versions) > 0:
                    # only add to choices if datastore has at least one version
                    version_choices = ()
                    for v in versions:
                        if "inactive" in v.name:
                            continue
                        selection_text = ds.name + ',' + v.name
                        version_choices = (version_choices +
                                           ((selection_text, v.name),))
                        self._add_attr_to_optional_fields(ds.name,
                                                          selection_text)
                    datastore_choices = (ds.name, version_choices)
                    choices = choices + (datastore_choices,)
        return choices

    def _add_attr_to_optional_fields(self, datastore, selection_text):
        fields = []
        if db_capability.is_mongodb_datastore(datastore):
            fields = self.mongodb_fields
        elif db_capability.is_vertica_datastore(datastore):
            fields = self.vertica_fields

        for field in fields:
            attr_key = 'data-datastore-' + selection_text
            widget = self.fields[field[0]].widget
            if attr_key not in widget.attrs:
                widget.attrs[attr_key] = field[1]

    def _get_users(self, data):
        users = None
        if data.get('user'):
            user = {
                'name': data['user'],
                'password': data['initial_pass'],
            }
            users = [user]
        return users

    def handle(self, request, data):
        try:
            datastore = data['datastore'].split(',')[0]
            datastore_version = data['datastore'].split(',')[1]

            final_flavor = data['flavor']
            if db_capability.is_vertica_datastore(datastore):
                final_flavor = data['vertica_flavor']

            LOG.info("Launching cluster with parameters "
                     "{name=%s, volume=%s, flavor=%s, "
                     "datastore=%s, datastore_version=%s, "
                     "cluster_user=%s, num_instances=%s}",
                     data['name'], data['volume'], final_flavor,
                     datastore, datastore_version, data['user'],
                     data['num_instances'])
            api.trove.cluster_create(request,
                                     data['name'],
                                     data['volume'],
                                     final_flavor,
                                     data['num_instances'],
                                     datastore=datastore,
                                     datastore_version=datastore_version,
                                     users=self._get_users(data)
                                     )

            messages.success(request,
                             _('Launched cluster "%s"') % data['name'])
            return True
        except Exception as e:
            redirect = reverse("horizon:project:database_clusters:index")
            exceptions.handle(request, _('Unable to launch cluster. %s')
                              % e.message, redirect=redirect)


class AddShardForm(forms.SelfHandlingForm):
    name = forms.CharField(
        label=_("Cluster Name"),
        max_length=80,
        widget=forms.TextInput(attrs={'readonly': 'readonly'}))
    num_shards = forms.IntegerField(
        label=_("Number of Shards"),
        initial=1,
        widget=forms.TextInput(attrs={'readonly': 'readonly'}))
    num_instances = forms.IntegerField(label=_("Instances Per Shard"),
                                       initial=3,
                                       widget=forms.TextInput(
                                           attrs={'readonly': 'readonly'}))
    cluster_id = forms.CharField(required=False,
                                 widget=forms.HiddenInput())

    def handle(self, request, data):
        try:
            LOG.info("Adding shard with parameters "
                     "{name=%s, num_shards=%s, num_instances=%s, "
                     "cluster_id=%s}",
                     data['name'],
                     data['num_shards'],
                     data['num_instances'],
                     data['cluster_id'])
            api.trove.cluster_add_shard(request, data['cluster_id'])

            messages.success(request,
                             _('Added shard to "%s"') % data['name'])
        except Exception as e:
            redirect = reverse("horizon:project:database_clusters:index")
            exceptions.handle(request, _('Unable to add shard. %s')
                              % e.message, redirect=redirect)
        return True


class ResetPasswordForm(forms.SelfHandlingForm):
    cluster_id = forms.CharField(widget=forms.HiddenInput())
    username = forms.CharField(label=_('Username'),
                               required=True,
                               help_text=_("Reset password for this user"))
    password = forms.CharField(widget=forms.PasswordInput(),
                               label=_("New Password"),
                               required=True,
                               help_text=_("New password for cluster access"))

    def handle(self, request, data):
        user = data.get('username')
        password = data.get("password")
        cluster_id = data.get("cluster_id")
        try:
            api.trove.cluster_edit_admin(request,
                                         cluster_id,
                                         user,
                                         password)
            messages.success(request,
                             _('Resetting password "%s"') % cluster_id)
        except Exception as e:
            redirect = reverse("horizon:project:database_clusters:index")
            exceptions.handle(request, _('Unable to reset password. %s') %
                              e.message, redirect=redirect)
        return True
