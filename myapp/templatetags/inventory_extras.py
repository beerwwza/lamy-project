from django import template

register = template.Library()

@register.filter
def get(d, key):
    """dict lookup: {{ my_dict|get:key }}"""
    if isinstance(d, dict):
        return d.get(key, {})
    return {}
