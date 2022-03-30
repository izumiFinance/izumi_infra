import json
from django.utils.safestring import mark_safe
from pygments import highlight
from pygments.lexers import JsonLexer
from pygments.formatters import HtmlFormatter


def json_prettify_styles():
    """
    Used to generate Pygment styles (to be included in a .CSS file) as follows:
        print(json_prettify_styles())
    """
    formatter = HtmlFormatter(style='colorful')
    return formatter.get_style_defs()


def json_prettify(json_data):
    """
    Adapted from:
    https://www.pydanny.com/pretty-formatting-json-django-admin.html
    """

    # Get the Pygments formatter
    formatter = HtmlFormatter(style='colorful')

    # Highlight the data
    json_text = highlight(
        json.dumps(json_data, sort_keys=True, indent=2),
        JsonLexer(),
        formatter
    )

    # Get the stylesheet
    style = "<style>" + formatter.get_style_defs() + "</style>"

    # Safe the output
    return mark_safe(style + json_text)
