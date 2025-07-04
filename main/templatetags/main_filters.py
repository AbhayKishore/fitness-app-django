from django import template
from main.models import Exercise

register = template.Library()

@register.filter
def dict_get(dictionary, key):
    return dictionary.get(key)

@register.filter
def exercise_obj(value):
    try:
        return Exercise.objects.get(exercise_name=value)
    except Exercise.DoesNotExist:
        return None