from pygments.token import string_to_tokentype
from pygments.style import Style
from pygments.util import ClassNotFound
from prompt_toolkit.styles import PygmentsStyle,default_style_extensions
from pygments.styles import get_style_by_name


def style_factory(name, cli_style):
    try:
        style = get_style_by_name(name)
    except ClassNotFound:
        style = get_style_by_name('native')

    class VStyle(Style):
        styles = {}

        styles.update(style.styles)
        styles.update(default_style_extensions)
        custom_styles = dict([(string_to_tokentype(x), y)
                                for x, y in cli_style.items()])
        styles.update(custom_styles)
    return PygmentsStyle(VStyle)
