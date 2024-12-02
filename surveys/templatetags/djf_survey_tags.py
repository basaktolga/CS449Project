from django import template
from surveys.models import Question, Section  # Import the models
from surveys.utils import create_star  # Correct import

register = template.Library()


@register.filter(name='addclass')
def addclass(field, css):
    """Add CSS class to a form field"""
    return field.as_widget(attrs={"class": css})


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


from surveys.utils import create_star as utils_create_star  # Rename the imported function

@register.simple_tag
def create_star(number, id_element, num_stars):
    return utils_create_star(active_star=int(number), num_stars=num_stars, id_element=id_element)


@register.filter
def get_hover_text(field):
    """Get the hover text for a field if it exists"""
    try:
        field_name = field.name
        question_id = field_name.split('_')[-1]
        if question_id.isdigit():
            question = Question.objects.get(id=int(question_id))
            return question.hover_text
    except (Question.DoesNotExist, AttributeError, IndexError):
        pass
    return None


@register.filter
def get_section(field):
    """Get the section for a field if it exists"""
    try:
        # Extract the question ID from the field name
        field_name = field.name  # This should be something like 'field_survey_123'
        question_id = field_name.split('_')[-1]  # Get the last part (question ID)
        
        if question_id.isdigit():
            question = Question.objects.get(id=int(question_id))
            return question.section
    except (Question.DoesNotExist, AttributeError, IndexError):
        pass
    return None


@register.filter
def get_section_id(section):
    """Get the section ID, handling None case"""
    return section.id if section else 0
