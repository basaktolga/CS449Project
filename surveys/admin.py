from django.contrib import admin
from .models import Survey, Question, Answer, UserAnswer, TermsValidators, ConsentFormContent, Section


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


class SectionInline(admin.TabularInline):
    model = Section
    extra = 1


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1


@admin.register(Survey)
class SurveyAdmin(admin.ModelAdmin):
    inlines = [SectionInline]
    list_display = ('name', 'slug')
    search_fields = ('name', 'slug')


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ['name', 'survey', 'ordering']
    list_filter = ['survey']
    search_fields = ['name', 'survey__name']
    ordering = ['survey', 'ordering']

admin.site.register(ConsentFormContent)
admin.site.register(Question, AdminQuestion)
admin.site.register(Answer, AdminAnswer)
admin.site.register(UserAnswer, AdminUserAnswer)
admin.site.register(TermsValidators, AdminTermsValidator)
