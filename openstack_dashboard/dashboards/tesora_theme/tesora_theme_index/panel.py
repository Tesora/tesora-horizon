import horizon

from openstack_dashboard.dashboards.tesora_theme import dashboard

class TesoraThemePanel(horizon.Panel):
    name = "Panel providing the Tesora theme"
    slug = 'tesora_theme_index'
    nav = True

dashboard.TesoraTheme.register(TesoraThemePanel)
