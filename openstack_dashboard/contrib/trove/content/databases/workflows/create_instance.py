# Copyright 2013 Rackspace Hosting
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
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon.utils import memoized
from horizon import workflows
from openstack_dashboard import api as dash_api
from openstack_dashboard.contrib.trove import api

from openstack_dashboard.contrib.trove.content.databases import db_capability
from openstack_dashboard.dashboards.project.instances \
    import utils as instance_utils


LOG = logging.getLogger(__name__)


class SetInstanceDetailsAction(workflows.Action):
    name = forms.CharField(max_length=80, label=_("Instance Name"))
    volume = forms.IntegerField(label=_("Volume Size"),
                                min_value=0,
                                initial=1,
                                help_text=_("Size of the volume in GB."))
    volume_type = forms.ChoiceField(
        label=_("Volume Type"),
        required=False,
        help_text=_("Applicable only if the volume size is specified."))
    datastore = forms.ChoiceField(
        label=_("Datastore"),
        help_text=_("Type and version of datastore."),
        widget=forms.Select(attrs={
            'class': 'switchable',
            'data-slug': 'datastore'
        }))

    class Meta(object):
        name = _("Details")
        help_text_template = "project/databases/_launch_details_help.html"

    def clean(self):
        datastore_and_version = self.data.get("datastore", None)
        if not datastore_and_version:
            msg = _("You must select a datastore type and version.")
            self._errors["datastore"] = self.error_class([msg])
        else:
            datastore, datastore_version = self._parse_datastore_display_text(
                datastore_and_version)
            field_name = self._build_flavor_field_name(datastore,
                                                       datastore_version)
            flavor = self.data.get(field_name, None)
            if not flavor:
                msg = _("You must select a flavor.")
                self._errors[field_name] = self.error_class([msg])

        return self.cleaned_data

    def handle(self, request, context):
        datastore_and_version = context["datastore"]
        if datastore_and_version:
            datastore, datastore_version = self._parse_datastore_display_text(
                datastore_and_version)
            field_name = self._build_flavor_field_name(datastore,
                                                       datastore_version)
            flavor = self.data[field_name]
            if flavor:
                context["flavor"] = flavor
                return context
        return None

    @memoized.memoized_method
    def datastore_flavors(self, request, datastore_name, datastore_version):
        try:
            return api.trove.datastore_flavors(
                request, datastore_name, datastore_version)
        except Exception:
            LOG.exception("Exception while obtaining flavors list")
            self._flavors = []
            redirect = reverse('horizon:project:database_clusters:index')
            exceptions.handle(request,
                              _('Unable to obtain flavors.'),
                              redirect=redirect)

    @memoized.memoized_method
    def volume_types(self, request):
        try:
            return dash_api.cinder.volume_type_list(request)
        except Exception:
            LOG.exception("Exception while obtaining volume types list")
            self._volume_types = []

    def populate_volume_type_choices(self, request, context):
        try:
            volume_types = self.volume_types(request)
            return ([("no_type", _("No volume type"))] +
                    [(type.name, type.name)
                     for type in volume_types])
        except Exception:
            LOG.exception("Exception while obtaining volume types list")
            self._volume_types = []

    @memoized.memoized_method
    def datastores(self, request):
        try:
            return api.trove.datastore_list(request)
        except Exception:
            LOG.exception("Exception while obtaining datastores list")
            self._datastores = []

    @memoized.memoized_method
    def datastore_versions(self, request, datastore):
        try:
            return api.trove.datastore_version_list(request, datastore)
        except Exception:
            LOG.exception("Exception while obtaining datastore version list")
            self._datastore_versions = []

    def populate_datastore_choices(self, request, context):
        choices = ()
        datastores = self.datastores(request)
        if datastores is not None:
            for ds in datastores:
                versions = self.datastore_versions(request, ds.name)
                if versions:
                    # only add to choices if datastore has at least one version
                    version_choices = ()
                    for v in versions:
                        if "inactive" in v.name:
                            continue
                        selection_text = self._build_datastore_display_text(
                            ds.name, v.name)
                        widget_text = self._build_widget_field_name(
                            ds.name, v.name)
                        version_choices = (version_choices +
                                           ((widget_text, selection_text),))
                        self._add_datastore_flavor_field(request,
                                                         ds.name,
                                                         v.name)
                    choices = choices + version_choices
        return choices

    def _add_datastore_flavor_field(self,
                                    request,
                                    datastore,
                                    datastore_version):
        name = self._build_widget_field_name(datastore, datastore_version)
        attr_key = 'data-datastore-' + name
        field_name = self._build_flavor_field_name(datastore,
                                                   datastore_version)
        self.fields[field_name] = forms.ChoiceField(
            label=_("Flavor"),
            help_text=_("Size of image to launch."),
            required=False,
            widget=forms.Select(attrs={
                'class': 'switched',
                'data-switch-on': 'datastore',
                attr_key: _("Flavor")
            }))
        valid_flavors = self.datastore_flavors(request,
                                               datastore,
                                               datastore_version)
        if valid_flavors:
            self.fields[field_name].choices = instance_utils.sort_flavor_list(
                request, valid_flavors)

    def _build_datastore_display_text(self, datastore, datastore_version):
        return datastore + ' - ' + datastore_version

    def _parse_datastore_display_text(self, datastore_and_version):
        if datastore_and_version:
            datastore = datastore_and_version.split('-')[0]
            datastore_version = datastore_and_version.split('-')[1]
            return datastore.strip(), datastore_version.strip()
        return None, None

    def _build_widget_field_name(self, datastore, datastore_version):
        return self._build_datastore_display_text(
            datastore, datastore_version).replace(' ', '')

    def _build_flavor_field_name(self, datastore, datastore_version):
        return self._build_widget_field_name(
            datastore, datastore_version).replace('.', '_')


TROVE_ADD_USER_PERMS = getattr(settings, 'TROVE_ADD_USER_PERMS', [])
TROVE_ADD_DATABASE_PERMS = getattr(settings, 'TROVE_ADD_DATABASE_PERMS', [])
TROVE_ADD_PERMS = TROVE_ADD_USER_PERMS + TROVE_ADD_DATABASE_PERMS


class SetInstanceDetails(workflows.Step):
    action_class = SetInstanceDetailsAction
    contributes = ("name", "volume", "volume_type", "flavor", "datastore")


class SetNetworkAction(workflows.Action):
    network = forms.MultipleChoiceField(label=_("Networks"),
                                        widget=forms.CheckboxSelectMultiple(),
                                        error_messages={
                                            'required': _(
                                                "At least one network must"
                                                " be specified.")},
                                        help_text=_("Launch instance with"
                                                    " these networks"))

    def __init__(self, request, *args, **kwargs):
        super(SetNetworkAction, self).__init__(request, *args, **kwargs)
        network_list = self.fields["network"].choices
        if len(network_list) == 1:
            self.fields['network'].initial = [network_list[0][0]]

    class Meta(object):
        name = _("Networking")
        permissions = ('openstack.services.network',)
        help_text = _("Select networks for your instance.")

    def populate_network_choices(self, request, context):
        try:
            tenant_id = self.request.user.tenant_id
            networks = dash_api.neutron.network_list_for_tenant(request,
                                                                tenant_id)
            network_list = [(network.id, network.name_or_id)
                            for network in networks]
        except Exception:
            network_list = []
            exceptions.handle(request,
                              _('Unable to retrieve networks.'))
        return network_list


class SetNetwork(workflows.Step):
    action_class = SetNetworkAction
    template_name = "project/databases/_launch_networks.html"
    contributes = ("network_id",)

    def contribute(self, data, context):
        if data:
            networks = self.workflow.request.POST.getlist("network")
            # If no networks are explicitly specified, network list
            # contains an empty string, so remove it.
            networks = [n for n in networks if n != '']
            if networks:
                context['network_id'] = networks

        return context


class AddDatabasesAction(workflows.Action):
    """Initialize the database with users/databases. This tab will honor
    the settings which should be a list of permissions required:

    * TROVE_ADD_USER_PERMS = []
    * TROVE_ADD_DATABASE_PERMS = []
    """
    databases = forms.CharField(label=_('Initial Databases'),
                                required=False,
                                help_text=_('Comma separated list of '
                                            'databases to create'))
    user = forms.CharField(label=_('Initial Admin User'),
                           required=False,
                           help_text=_("Initial admin user to add"))
    password = forms.CharField(widget=forms.PasswordInput(),
                               label=_("Password"),
                               required=False)
    host = forms.CharField(label=_("Allowed Host (optional)"),
                           required=False,
                           help_text=_("Host or IP that the user is allowed "
                                       "to connect through."))

    class Meta(object):
        name = _("Initialize Databases")
        permissions = TROVE_ADD_PERMS
        help_text_template = "project/databases/_launch_initialize_help.html"

    def clean(self):
        cleaned_data = super(AddDatabasesAction, self).clean()
        if cleaned_data.get('user'):
            if not cleaned_data.get('password'):
                msg = _('You must specify a password if you create a user.')
                self._errors["password"] = self.error_class([msg])
            if db_capability.db_required_when_creating_user(
                    self.data[u'datastore']):
                if not cleaned_data.get('databases'):
                    msg = _('You must specify at least one database if '
                            'you create a user.')
                    self._errors["databases"] = self.error_class([msg])
        return cleaned_data


class InitializeDatabase(workflows.Step):
    action_class = AddDatabasesAction
    contributes = ["databases", 'user', 'password', 'host']


class AdvancedAction(workflows.Action):
    config = forms.ChoiceField(
        label=_("Configuration Group"),
        required=False,
        help_text=_('Select a configuration group'))
    initial_state = forms.ChoiceField(
        label=_('Source for Initial State'),
        required=False,
        help_text=_("Choose initial state."),
        choices=[
            ('', _('None')),
            ('backup', _('Restore from Backup')),
            ('master', _('Replicate from Instance'))],
        widget=forms.Select(attrs={
            'class': 'switchable',
            'data-slug': 'initial_state'
        }))
    backup = forms.ChoiceField(
        label=_('Backup Name'),
        required=False,
        help_text=_('Select a backup to restore'),
        widget=forms.Select(attrs={
            'class': 'switched',
            'data-switch-on': 'initial_state',
            'data-initial_state-backup': _('Backup Name')
        }))
    master = forms.ChoiceField(
        label=_('Master Instance Name'),
        required=False,
        help_text=_('Select a master instance'),
        widget=forms.Select(attrs={
            'class': 'switched',
            'data-switch-on': 'initial_state',
            'data-initial_state-master': _('Master Instance Name')
        }))
    replica_count = forms.IntegerField(
        label=_('Replica Count'),
        required=False,
        min_value=1,
        initial=1,
        help_text=_('Specify the number of replicas to be created'),
        widget=forms.TextInput(attrs={
            'class': 'switched',
            'data-switch-on': 'initial_state',
            'data-initial_state-master': _('Replica Count')
        }))

    class Meta(object):
        name = _("Advanced")
        help_text_template = "project/databases/_launch_advanced_help.html"

    def populate_config_choices(self, request, context):
        try:
            configs = api.trove.configuration_list(request)
            choices = [(c.id, c.name) for c in configs]
        except Exception:
            choices = []

        if choices:
            choices.insert(0, ("", _("Select configuration")))
        else:
            choices.insert(0, ("", _("No configurations available")))
        return choices

    def populate_backup_choices(self, request, context):
        try:
            backups = api.trove.backup_list(request)
            choices = [(b.id, b.name) for b in backups
                       if b.status == 'COMPLETED']
        except Exception:
            choices = []

        if choices:
            choices.insert(0, ("", _("Select backup")))
        else:
            choices.insert(0, ("", _("No backups available")))
        return choices

    def _get_instances(self):
        instances = []
        try:
            instances = api.trove.instance_list(self.request)
            marker = instances.next
            while marker or False:
                temp_instances = api.trove.instance_list(self.request,
                                                         marker=marker)
                marker = temp_instances.next
                instances.items += temp_instances.items
                instances.links = temp_instances.links
            instances.next = None
        except Exception:
            msg = _('Unable to retrieve database instances.')
            exceptions.handle(self.request, msg)
        return instances

    def populate_master_choices(self, request, context):
        try:
            instances = self._get_instances()
            choices = sorted([(i.id, i.name) for i in
                             instances if i.status == 'ACTIVE'],
                             key=lambda i: i[1])
        except Exception:
            choices = []

        if choices:
            choices.insert(0, ("", _("Select instance")))
        else:
            choices.insert(0, ("", _("No instances available")))
        return choices

    def clean(self):
        cleaned_data = super(AdvancedAction, self).clean()

        datastore = self.data[u'datastore']

        config = self.cleaned_data['config']
        if config:
            try:
                # Make sure the user is not "hacking" the form
                # and that they have access to this configuration
                cfg = api.trove.configuration_get(self.request, config)
                self.cleaned_data['config'] = cfg.id
            except Exception:
                raise forms.ValidationError(_("Unable to find configuration "
                                              "group!"))
        else:
            if db_capability.require_configuration_group(datastore):
                msg = _('This datastore requires a configuration group.')
                self._errors["config"] = self.error_class([msg])

        initial_state = cleaned_data.get("initial_state")

        if initial_state == 'backup':
            cleaned_data['replica_count'] = None
            if not db_capability.can_backup(datastore):
                msg = _('You cannot specify a backup for the initial state '
                        'for this datastore.')
                self._errors["initial_state"] = self.error_class([msg])
            else:
                backup = self.cleaned_data['backup']
                if backup:
                    try:
                        bkup = api.trove.backup_get(self.request, backup)
                        self.cleaned_data['backup'] = bkup.id
                    except Exception:
                        raise forms.ValidationError(
                            _("Unable to find backup!"))
                else:
                    msg = _("A backup must be selected!")
                    self._errors["backup"] = self.error_class([msg])

                cleaned_data['master'] = None
        elif initial_state == 'master':
            if not db_capability.can_launch_from_master(datastore):
                msg = _('You cannot specify a master for the initial state '
                        'for this datastore.')
                self._errors["initial_state"] = self.error_class([msg])
            else:
                master = self.cleaned_data['master']
                if master:
                    try:
                        api.trove.instance_get(self.request, master)
                    except Exception:
                        raise forms.ValidationError(
                            _("Unable to find master instance!"))
                else:
                    msg = _("A master instance must be selected!")
                    self._errors["master"] = self.error_class([msg])

                cleaned_data['backup'] = None
        else:
            cleaned_data['master'] = None
            cleaned_data['backup'] = None
            cleaned_data['replica_count'] = None

        return cleaned_data


class Advanced(workflows.Step):
    action_class = AdvancedAction
    contributes = ['config', 'backup', 'master', 'replica_count']


class LaunchInstance(workflows.Workflow):
    slug = "launch_instance"
    name = _("Launch Instance")
    finalize_button_name = _("Launch")
    success_message = _('Launched %(count)s named "%(name)s".')
    failure_message = _('Unable to launch %(count)s named "%(name)s".')
    success_url = "horizon:project:databases:index"
    default_steps = (SetInstanceDetails,
                     SetNetwork,
                     InitializeDatabase,
                     Advanced)

    def __init__(self, request=None, context_seed=None, entry_point=None,
                 *args, **kwargs):
        super(LaunchInstance, self).__init__(request, context_seed,
                                             entry_point, *args, **kwargs)
        self.attrs['autocomplete'] = (
            settings.HORIZON_CONFIG.get('password_autocomplete'))

    def format_status_message(self, message):
        name = self.context.get('name', 'unknown instance')
        return message % {"count": _("instance"), "name": name}

    def _get_databases(self, context):
        """Returns the initial databases for this instance."""
        databases = None
        db_value = context.get('databases')
        if db_value and db_value != u'':
            dbs = context['databases']
            databases = [{'name': d.strip()} for d in dbs.split(',')]
        return databases

    def _get_users(self, context):
        users = None
        if context.get('user'):
            user = {
                'name': context['user'],
                'password': context['password'],
            }
            dbs = self._get_databases(context)
            if dbs is not None:
                user['databases'] = dbs
            if context['host']:
                user['host'] = context['host']
            users = [user]
        return users

    def _get_backup(self, context):
        backup = None
        if context.get('backup'):
            backup = {'backupRef': context['backup']}
        return backup

    def _get_nics(self, context):
        netids = context.get('network_id', None)
        if netids:
            return [{"net-id": netid, "v4-fixed-ip": ""}
                    for netid in netids]
        else:
            return None

    def _get_config(self, context):
        config = None
        if context.get('config'):
            config = context['config']
        return config

    def _get_volume_type(self, context):
        volume_type = None
        if context.get('volume_type') != "no_type":
            volume_type = context['volume_type']
        return volume_type

    def handle(self, request, context):
        try:
            datastore = self.context['datastore'].split('-')[0]
            datastore_version = self.context['datastore'].split('-')[1]
            LOG.info("Launching database instance with parameters "
                     "{name=%s, volume=%s, volume_type=%s, flavor=%s, "
                     "datastore=%s, datastore_version=%s, "
                     "dbs=%s, users=%s, "
                     "backups=%s, nics=%s, "
                     "replica_of=%s, configuration=%s, replica_count=%s}",
                     context['name'], context['volume'],
                     context['volume_type'], context['flavor'],
                     datastore, datastore_version,
                     self._get_databases(context), self._get_users(context),
                     self._get_backup(context), self._get_nics(context),
                     context.get('master'), self._get_config(context),
                     context['replica_count'])
            api.trove.instance_create(request,
                                      context['name'],
                                      context['volume'],
                                      context['flavor'],
                                      datastore=datastore,
                                      datastore_version=datastore_version,
                                      databases=self._get_databases(context),
                                      users=self._get_users(context),
                                      restore_point=self._get_backup(context),
                                      nics=self._get_nics(context),
                                      replica_of=context.get('master'),
                                      configuration=self._get_config(context),
                                      replica_count=context['replica_count'],
                                      volume_type=self._get_volume_type(
                                          context))
            return True
        except Exception:
            exceptions.handle(request)
            return False
