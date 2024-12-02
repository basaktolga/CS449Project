from django.template import Library
from surveys.utils import create_star as utils_create_star
from django import template
from surveys.models import Question

register = Library()


@register.filter(name='addclass')
def addclass(field, class_attr):
    return field.as_widget(attrs={'class': class_attr})


@register.filter(name='get_id_field')
def get_id_field(field):
    try:
        if hasattr(field, 'auto_id'):
            parse = field.auto_id.split("_")
            try:
                return int(parse[-1])
            except (ValueError, TypeError):
                return None
        return None
    except (AttributeError, IndexError):
        return None


@register.simple_tag
def create_star(number, id_element, num_stars):
    return utils_create_star(active_star=int(number), num_stars=num_stars, id_element=id_element)


@register.filter
def get_hover_text(field):
    """Get the hover text for a field if it exists"""
    try:
        question_id = field.auto_id.split('_')[-1]
        if question_id.isdigit():
            question = Question.objects.get(id=question_id)
            return question.hover_text
    except (Question.DoesNotExist, AttributeError):
        pass
    return None
