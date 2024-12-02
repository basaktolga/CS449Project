from django.contrib import admin
from .models import Survey, Question, Answer, UserAnswer, TermsValidators, ConsentFormContent


class AdminQuestion(admin.ModelAdmin):
    list_display = ('survey', 'label', 'type_field', 'help_text', 'required', 'hover_text')
    search_fields = ('survey__name', )
    fields = (
        'label', 
        'survey', 
        'type_field', 
        'choices', 
        'help_text', 
        'hover_text', 
        'required', 
        'ordering', 
        'include_other'
    )


class AdminAnswer(admin.ModelAdmin):
    list_display = ('question', 'get_label', 'value', 'user_answer')
    search_fields = ('question__label', 'value',)
    list_filter = ('question__survey',)

    def get_label(self, obj):
        return obj.question.label
    get_label.admin_order_field = 'question'
    get_label.short_description = 'Label'


class AdminUserAnswer(admin.ModelAdmin):
    list_display = ('survey', 'user', 'created_at', 'updated_at')


class AdminSurvey(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name', 'slug')


class AdminTermsValidator(admin.ModelAdmin):
    list_display = ('question', 'terms')


class ConsentFormContentAdmin(admin.ModelAdmin):
    list_display = ('title',)

admin.site.register(ConsentFormContent)
admin.site.register(Survey, AdminSurvey)
admin.site.register(Question, AdminQuestion)
admin.site.register(Answer, AdminAnswer)
admin.site.register(UserAnswer, AdminUserAnswer)
admin.site.register(TermsValidators, AdminTermsValidator)
