from django.template import Library, Node, TemplateSyntaxError

register = Library()


@register.filter("zip")
def zip_string(str, elements_separator):
    """
    zip string separated by | char and items separated by *elements_separator*
    """
    lists = []
    for tmp_list in str.split("|"):
        lists.append(tmp_list.split(elements_separator))
    return zip(*lists)
