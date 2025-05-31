from django import template

register = template.Library()


@register.filter("startswith")
def startswith(text, starts):
    return text.startswith(starts)


@register.filter("get_value")
def get_value(dictionary, key):
    return dictionary.get(key)


@register.filter("replace_commas")
def replace_commas(string):
    val = str(string)
    return val.replace(",", "")
