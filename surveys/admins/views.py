import csv
from io import StringIO

from django.utils.text import capfirst
from django.utils.translation import gettext, gettext_lazy as _
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.detail import DetailView
from django.views.generic.edit import FormMixin
from django.utils.decorators import method_decorator
from django.contrib.admin.views.decorators import staff_member_required
from django.urls import reverse, reverse_lazy
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import View, DeleteView
from django.http import JsonResponse, HttpResponse
from django.contrib import messages

from surveys.app_settings import SURVEYS_ADMIN_BASE_PATH
from surveys.models import Survey, Question, UserAnswer, Section, TYPE_FIELD
from surveys.mixin import ContextTitleMixin
from surveys.views import SurveyListView
from surveys.forms import BaseSurveyForm
from surveys.summary import SummaryResponse
from surveys.admins.v2.forms import SurveyForm


@method_decorator(staff_member_required, name='dispatch')
class AdminCrateSurveyView(ContextTitleMixin, CreateView):
    template_name = 'surveys/admins/form.html'
    form_class = SurveyForm
    title_page = _("Add New Survey")

    def get_success_url(self):
        survey = self.object
        messages.success(self.request, gettext("%(page_action_name)s succeeded.") % dict(
            page_action_name=capfirst(self.title_page.lower())))
        return reverse("surveys:admin_forms_survey", args=[survey.slug])


@method_decorator(staff_member_required, name='dispatch')
class AdminEditSurveyView(ContextTitleMixin, UpdateView):
    model = Survey
    form_class = SurveyForm
    template_name = 'surveys/admins/form.html'
    title_page = _("Edit Survey")

    def get_success_url(self):
        survey = self.object
        messages.success(self.request, gettext("%(page_action_name)s succeeded.") % dict(
                        page_action_name=capfirst(self.title_page.lower())))
        return reverse("surveys:admin_forms_survey", args=[survey.slug])


@method_decorator(staff_member_required, name='dispatch')
class AdminSurveyListView(SurveyListView):
    template_name = 'surveys/admins/survey_list.html'


@method_decorator(staff_member_required, name='dispatch')
class AdminSurveyFormView(ContextTitleMixin, FormMixin, DetailView):
    model = Survey
    template_name = 'surveys/admins/form_preview.html'
    form_class = BaseSurveyForm

    def get_form(self, form_class=None):
        if form_class is None:
            form_class = self.get_form_class()
        return form_class(survey=self.object, user=self.request.user, **self.get_form_kwargs())

    def get_title_page(self):
        return self.object.name

    def get_sub_title_page(self):
        return self.object.description


@method_decorator(staff_member_required, name='dispatch')
class AdminDeleteSurveyView(DetailView):
    model = Survey

    def get(self, request, *args, **kwargs):
        survey = self.get_object()
        survey.delete()
        messages.success(request, gettext("Survey %ss succesfully deleted.") % survey.name)
        return redirect("surveys:admin_survey")


@method_decorator(staff_member_required, name='dispatch')
class AdminCreateQuestionView(ContextTitleMixin, CreateView):
    model = Question
    template_name = 'surveys/admins/question_form.html'
    success_url = reverse_lazy("surveys:")
    fields = ['label', 'key', 'type_field', 'choices', 'help_text', 'hover_text', 'required', 'section']
    title_page = _("Add Question")
    survey = None

    def dispatch(self, request, *args, **kwargs):
        self.survey = get_object_or_404(Survey, id=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['section'].queryset = Section.objects.filter(survey=self.survey)
        form.fields['section'].empty_label = _("No Section")
        return form

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            question = form.save(commit=False)
            question.survey = self.survey
            question.save()
            messages.success(self.request, gettext("%(page_action_name)s succeeded.") % dict(
                page_action_name=capfirst(self.title_page.lower())))
            return self.form_valid(form)
        else:
            return self.form_invalid(form)


@method_decorator(staff_member_required, name='dispatch')
class AdminUpdateQuestionView(ContextTitleMixin, UpdateView):
    model = Question
    template_name = 'surveys/admins/question_form.html'
    success_url = SURVEYS_ADMIN_BASE_PATH
    fields = ['label', 'key', 'type_field', 'choices', 'help_text', 'hover_text', 'required', 'section']
    title_page = _("Edit Question")
    survey = None

    def dispatch(self, request, *args, **kwargs):
        question = self.get_object()
        self.survey = question.survey
        return super().dispatch(request, *args, **kwargs)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['section'].queryset = Section.objects.filter(survey=self.survey)
        form.fields['section'].empty_label = _("No Section")
        return form


@method_decorator(staff_member_required, name='dispatch')
class AdminDeleteQuestionView(DetailView):
    model = Question
    survey = None

    def dispatch(self, request, *args, **kwargs):
        question = self.get_object()
        self.survey = question.survey
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        question = self.get_object()
        question.delete()
        messages.success(request, gettext("Question %ss succesfully deleted.") % question.label)
        return redirect("surveys:admin_forms_survey", slug=self.survey.slug)


@method_decorator(staff_member_required, name='dispatch')
class AdminChangeOrderQuestionView(View):
    def post(self, request, *args, **kwargs):
        ordering = request.POST['order_question'].split(",")
        for index, question_id in enumerate(ordering):
            if question_id:
                question = Question.objects.get(id=question_id)
                question.ordering = index
                question.save()

        data = {
            'message': gettext("Update ordering of questions succeeded.")
        }
        return JsonResponse(data, status=200)


@method_decorator(staff_member_required, name='dispatch')
class DownloadResponseSurveyView(DetailView):
    model = Survey

    def get(self, request, *args, **kwargs):
        survey = self.get_object()
        user_answers = UserAnswer.objects.filter(survey=survey)
        csv_buffer = StringIO()
        writer = csv.writer(csv_buffer)

        rows = []
        header = []
        for index, user_answer in enumerate(user_answers):
            if index == 0:
                header.append('user')
                header.append('update_at')

            rows.append(user_answer.user.username if user_answer.user else 'no auth')
            rows.append(user_answer.updated_at.strftime("%Y-%m-%d %H:%M:%S"))
            
            for answer in user_answer.answer_set.all():
                if index == 0:
                    header.append(answer.question.label)
                    if answer.question.type_field == TYPE_FIELD.radio and answer.question.include_other:
                        header.append(f"{answer.question.label} - Other")

                if answer.question.type_field == TYPE_FIELD.radio and answer.question.include_other:
                    # Get the list of valid choices
                    choices = [choice.strip().lower() for choice in answer.question.choices.split(',')]
                    answer_value = answer.value.lower()
                    
                    # Check if the answer is in choices
                    if answer_value not in choices:
                        # This must be an "other" response
                        rows.append('Other')
                        rows.append(answer.value)  # The value itself is the "other" text
                    else:
                        rows.append(answer.get_value_for_csv)
                        rows.append('')  # Empty "other" column
                else:
                    rows.append(answer.get_value_for_csv)

            if index == 0:
                writer.writerow(header)
            writer.writerow(rows)
            rows = []

        response = HttpResponse(csv_buffer.getvalue(), content_type="text/csv")
        response['Content-Disposition'] = f'attachment; filename={survey.slug}.csv'
        return response


@method_decorator(staff_member_required, name='dispatch')
class SummaryResponseSurveyView(ContextTitleMixin, DetailView):
    model = Survey
    template_name = "surveys/admins/summary.html"
    title_page = _("Summary")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        summary = SummaryResponse(survey=self.get_object())
        context['summary'] = summary
        return context


@method_decorator(staff_member_required, name='dispatch')
class AdminCreateSectionView(ContextTitleMixin, CreateView):
    model = Section
    template_name = 'surveys/admins/section_form.html'
    fields = ['name', 'description', 'ordering']
    title_page = _("Add Section")
    survey = None

    def dispatch(self, request, *args, **kwargs):
        self.survey = get_object_or_404(Survey, slug=kwargs['slug'])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.survey = self.survey
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("surveys:admin_forms_survey", args=[self.survey.slug])


@method_decorator(staff_member_required, name='dispatch')
class AdminUpdateSectionView(ContextTitleMixin, UpdateView):
    model = Section
    template_name = 'surveys/admins/section_form.html'
    fields = ['name', 'description', 'ordering']
    title_page = _("Edit Section")

    def get_success_url(self):
        return reverse("surveys:admin_forms_survey", args=[self.object.survey.slug])


@method_decorator(staff_member_required, name='dispatch')
class AdminDeleteSectionView(DeleteView):
    model = Section
    template_name = 'surveys/admins/confirm_delete.html'
    context_object_name = 'section'

    def get_success_url(self):
        messages.success(self.request, _("Section deleted successfully."))
        return reverse_lazy('surveys:admin_forms_survey', args=[self.object.survey.slug])


@method_decorator(staff_member_required, name='dispatch')
class AdminChangeOrderSectionView(View):
    def post(self, request, *args, **kwargs):
        try:
            order_sections = request.POST.get('order_section', '').split(',')
            sections = []
            
            for idx, section_id in enumerate(order_sections, start=1):
                if section_id.isdigit():
                    section = Section.objects.get(id=int(section_id.replace('section_', '')))
                    section.ordering = idx
                    sections.append(section)
            
            Section.objects.bulk_update(sections, ['ordering'])
            
            return JsonResponse({
                'status': 'success',
                'message': _('Section order updated successfully.')
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
