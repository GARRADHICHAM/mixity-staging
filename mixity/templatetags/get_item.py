from django.template.defaulttags import register


@register.filter
def get_item(dictionary, key):
    if isinstance(dictionary, list):
        return key < len(dictionary) and dictionary[int(key)] or None
    return dictionary.get(key)
