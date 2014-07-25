import horizon


class TesoraTheme(horizon.Dashboard):
    name = "tesora_theme"
    slug = "tesora_theme"
    panels = ('tesora_theme_index', )
    default_panel = 'tesora_theme_index'
    nav = False

horizon.register(TesoraTheme)
