from django import template

register = template.Library()

@register.filter
def dict_key(dictionary, key):
    """Fetch value from dictionary using key."""
    return dictionary.get(key, "No data available")
