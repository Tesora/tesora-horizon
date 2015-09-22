# The slug of the panel to be added to HORIZON_CONFIG. Required.
PANEL = 'database_clusters'
# The slug of the dashboard the PANEL associated with. Required.
PANEL_DASHBOARD = 'project'
# The slug of the panel group the PANEL is associated with.
PANEL_GROUP = 'tesora_database'

# Python panel class of the PANEL to be added.
ADD_PANEL = ('tesora_horizon.openstack_dashboard.dashboards.'
             'project.database_clusters.panel.Clusters')
