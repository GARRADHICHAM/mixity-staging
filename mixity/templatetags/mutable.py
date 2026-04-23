from django.template.defaulttags import register

"""
    Extend functionalities of the define function. define function is scoped, so if we want to globally use a variable
    in the template, we can create a ref placed at the top most scope (if or for)
"""


class MutableRef:
    def __init__(self, obj):
        self.value = obj


# {% define "YourValue"|declare as your_variable %}
@register.filter
def declare(obj):
    return MutableRef(obj)


# {{ your_variable|update:"YourNewValue" }}
# update returns an empty string
@register.filter
def update(mutable_obj, new_value):
    mutable_obj.value = new_value
    return ""
