from django import template

from izumi_infra.utils.admin_utils import json_prettify

register = template.Library()

@register.filter
def json_prettify_filter(value):
    return json_prettify(value)
