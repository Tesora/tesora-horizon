# Copyright 2014 Tesora Inc.
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
from django.forms import ValidationError  # noqa
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages
from horizon.utils import validators
from openstack_dashboard.contrib.trove import api
from openstack_dashboard.contrib.trove.content.databases import db_capability


class CreateDatabaseForm(forms.SelfHandlingForm):
    instance_id = forms.CharField(widget=forms.HiddenInput())
    name = forms.CharField(max_length=80, label=_("Name"))
    character_set = forms.CharField(
        max_length=80, label=_("Character Set"), required=False,
        help_text=_("Optional character set for the database."))
    collation = forms.CharField(
        max_length=80, label=_("Collation"), required=False,
        help_text=_("Optional collation type for the database."))

    def handle(self, request, data):
        instance = data.get('instance_id')
        try:
            api.trove.database_create(request, instance, data['name'],
                                      data['character_set'],
                                      data['collation'])

            messages.success(request,
                             _('Created database "%s"') % data['name'])
        except Exception as e:
            redirect = reverse("horizon:project:databases:detail",
                               args=(instance,))
            exceptions.handle(request, _('Unable to create database. %s') %
                              e.message, redirect=redirect)
        return True


class ResizeVolumeForm(forms.SelfHandlingForm):
    instance_id = forms.CharField(widget=forms.HiddenInput())
    orig_size = forms.IntegerField(
        label=_("Current Size (GB)"),
        widget=forms.TextInput(attrs={'readonly': 'readonly'}),
        required=False,
    )
    new_size = forms.IntegerField(label=_("New Size (GB)"))

    def clean(self):
        cleaned_data = super(ResizeVolumeForm, self).clean()
        new_size = cleaned_data.get('new_size')
        if new_size <= self.initial['orig_size']:
            raise ValidationError(
                _("New size for volume must be greater than current size."))

        return cleaned_data

    def handle(self, request, data):
        instance = data.get('instance_id')
        try:
            api.trove.instance_resize_volume(request,
                                             instance,
                                             data['new_size'])

            messages.success(request, _('Resizing volume "%s"') % instance)
        except Exception as e:
            redirect = reverse("horizon:project:databases:index")
            exceptions.handle(request, _('Unable to resize volume. %s') %
                              e.message, redirect=redirect)
        return True


class ResizeInstanceForm(forms.SelfHandlingForm):
    instance_id = forms.CharField(widget=forms.HiddenInput())
    old_flavor_name = forms.CharField(label=_("Old Flavor"),
                                      required=False,
                                      widget=forms.TextInput(
                                      attrs={'readonly': 'readonly'}))
    new_flavor = forms.ChoiceField(label=_("New Flavor"),
                                   help_text=_("Choose a new instance "
                                               "flavor."))

    def __init__(self, request, *args, **kwargs):
        super(ResizeInstanceForm, self).__init__(request, *args, **kwargs)

        old_flavor_id = kwargs.get('initial', {}).get('old_flavor_id')
        choices = kwargs.get('initial', {}).get('flavors')
        # Remove current flavor from the list of flavor choices
        choices = [(flavor_id, name) for (flavor_id, name) in choices
                   if flavor_id != old_flavor_id]
        if choices:
            choices.insert(0, ("", _("Select a new flavor")))
        else:
            choices.insert(0, ("", _("No flavors available")))
        self.fields['new_flavor'].choices = choices

    def handle(self, request, data):
        instance = data.get('instance_id')
        flavor = data.get('new_flavor')
        try:
            api.trove.instance_resize(request, instance, flavor)

            messages.success(request, _('Resizing instance "%s"') % instance)
        except Exception as e:
            redirect = reverse("horizon:project:databases:index")
            exceptions.handle(request, _('Unable to resize instance. %s') %
                              e.message, redirect=redirect)
        return True


class AttachConfigurationForm(forms.SelfHandlingForm):
    instance_id = forms.CharField(widget=forms.HiddenInput())
    configuration = forms.ChoiceField(label=_("Configuration Groups"),
                                      required=True)

    def __init__(self, request, *args, **kwargs):
        super(AttachConfigurationForm, self).__init__(request, *args, **kwargs)
        instance_id = kwargs.get('initial', {}).get('instance_id')
        datastore = kwargs.get('initial', {}).get('datastore')
        datastore_version = kwargs.get('initial', {}).get('datastore_version')
        self.fields['instance_id'].initial = instance_id

        configurations = api.trove.configuration_list(request)
        choices = [(c.id, c.name) for c in configurations
                   if (c.datastore_name == datastore and
                       c.datastore_version_name == datastore_version)]
        if choices:
            choices.insert(0, ("", _("Select configuration group")))
        else:
            choices.insert(0, ("", _("No configuration groups available")))
        self.fields['configuration'].choices = choices

    def handle(self, request, data):
        instance_id = data.get('instance_id')
        try:
            api.trove.instance_attach_configuration(request,
                                                    instance_id,
                                                    data['configuration'])

            messages.success(request, _('Attaching Configuration group "%s"')
                             % instance_id)
        except Exception as e:
            redirect = reverse("horizon:project:databases:index")
            exceptions.handle(request, _('Unable to attach configuration '
                                         'group. %s')
                              % e.message, redirect=redirect)
        return True


class PromoteToReplicaSourceForm(forms.SelfHandlingForm):
    instance_id = forms.CharField(widget=forms.HiddenInput())

    def handle(self, request, data):
        instance_id = data.get('instance_id')
        name = self.initial['replica'].name
        try:
            api.trove.promote_to_replica_source(request, instance_id)
            messages.success(
                request,
                _('Promoted replica "%s" as the new replica source.') % name)
        except Exception as e:
            redirect = reverse("horizon:project:databases:index")
            exceptions.handle(
                request,
                _('Unable to promote replica as the new replica source.  "%s"')
                % e.message, redirect=redirect)
        return True


class CreateUserForm(forms.SelfHandlingForm):
    instance_id = forms.CharField(widget=forms.HiddenInput())
    name = forms.CharField(max_length=80, label=_("Name"))
    password = forms.RegexField(
        label=_("Password"),
        widget=forms.PasswordInput(render_value=False),
        regex=validators.password_validator(),
        error_messages={'invalid': validators.password_validator_msg()})
    host = forms.CharField(
        max_length=80, label=_("Host"), required=False,
        help_text=_("Optional host of user."))
    databases = forms.CharField(
        label=_('Initial Databases'), required=False,
        help_text=_('Comma separated list of databases user has access to.'))

    def handle(self, request, data):
        instance = data.get('instance_id')
        try:
            api.trove.user_create(
                request,
                instance,
                data['name'],
                data['password'],
                data['host'],
                self._get_databases(data))

            messages.success(request,
                             _('Created user "%s"') % data['name'])
        except Exception as e:
            redirect = reverse("horizon:project:databases:detail",
                               args=(instance,))
            exceptions.handle(request, _('Unable to create user. %s') %
                              e.message, redirect=redirect)
        return True

    def _get_databases(self, data):
        databases = []
        db_value = data['databases']
        if db_value and db_value != u'':
            dbs = data['databases']
            databases = [{'name': d.strip()} for d in dbs.split(',')]
        return databases


class EditUserForm(forms.SelfHandlingForm):
    instance_id = forms.CharField(widget=forms.HiddenInput())
    user_name = forms.CharField(
        max_length=80, label=_("Name"), required=False,
        widget=forms.TextInput(attrs={'readonly': 'readonly'}))
    user_host = forms.CharField(
        max_length=80, label=_("Host"), required=False,
        widget=forms.TextInput(attrs={'readonly': 'readonly'}))
    new_name = forms.CharField(
        max_length=80, label=_("New Name"), required=False)
    password = forms.RegexField(
        label=_("New Password"), required=False,
        widget=forms.PasswordInput(render_value=False),
        regex=validators.password_validator(),
        error_messages={'invalid': validators.password_validator_msg()})
    host = forms.CharField(
        max_length=80, label=_("New Host"), required=False,
        help_text=_("Optional host of user."))

    validation_err_msg = \
        _('A new name or new password or new host must be specified')

    def handle(self, request, data):
        instance_id = data.get('instance_id')
        try:
            instance = api.trove.instance_get(request, instance_id)

            api.trove.user_update_attributes(
                request,
                instance_id,
                self._get_user_name(instance.datastore['type'],
                                    data['user_name'],
                                    data['user_host']),
                data['new_name'],
                data['password'],
                data['host'])

            messages.success(request,
                             _('Updated user "%s"') % data['user_name'])
        except Exception as e:
            redirect = reverse("horizon:project:databases:detail",
                               args=(instance_id,))
            exceptions.handle(request, _('Unable to update user. %s') %
                              e.message, redirect=redirect)
        return True

    def clean(self):
        cleaned_data = super(EditUserForm, self).clean()

        if not cleaned_data['new_name'] and not cleaned_data['password'] and \
           not cleaned_data['host']:
            raise ValidationError(self.validation_err_msg)

        return cleaned_data

    def _get_user_name(self, datastore, user_name, user_host):
        return db_capability.get_fully_qualified_username(
            datastore, user_name, user_host)
