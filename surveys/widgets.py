from django import forms
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _


class CheckboxSelectMultipleSurvey(forms.CheckboxSelectMultiple):
    option_template_name = 'surveys/widgets/checkbox_option.html'


class RadioSelectSurvey(forms.RadioSelect):
    option_template_name = 'surveys/widgets/radio_option.html'
    
    def __init__(self, *args, include_other=False, **kwargs):
        self.include_other = include_other
        super().__init__(*args, **kwargs)
    
    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex, attrs)
        if value == 'other' and self.include_other:
            other_input = mark_safe(f'''
                <div>
                    <input type="text" 
                        name="{name}_other"
                        class="w-48 border-gray-200 rounded-lg p-1.5"
                        placeholder="Other, please specify"
                        onclick="document.getElementById('{option['attrs']['id']}').checked = true;"
                        onfocus="document.getElementById('{option['attrs']['id']}').checked = true;">
                </div>
            ''')
            option['label'] = other_input
            option['choice_label'] = other_input
        return option


class DateSurvey(forms.DateTimeInput):
    template_name = 'surveys/widgets/datepicker.html'


class RatingSurvey(forms.HiddenInput):
    template_name = 'surveys/widgets/star_rating.html'
    stars = 8

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context['widget']['num_ratings'] = self.num_ratings
        return context

class InlineChoiceField(forms.HiddenInput):
    template_name = 'surveys/widgets/inline_choices.html'
    extra = 3

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        if context['widget']['value']:
            context['widget']['choice_value'] = [x.strip() for x in context['widget']['value'].split(',')] 
        else:
            context['widget']['choice_value'] = []

        choices_count = len(context['widget']['choice_value'])
        context['widget']['extra'] = range(1 + choices_count, self.extra + 1 + choices_count)
        return context
