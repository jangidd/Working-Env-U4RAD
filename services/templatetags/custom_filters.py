# services/templatetags/custom_filters.py

from django import template

register = template.Library()

@register.filter
def sum_attribute(items, attr):
    return sum(getattr(item, attr) for item in items)