from django import template

register = template.Library()

@register.filter
def getattribute(obj, attr):
    """Gets an attribute of an object dynamically from a string name"""
    try:
        return obj[attr]
    except (KeyError, TypeError):
        try:
            return getattr(obj, attr)
        except (AttributeError, TypeError):
            return None 