from django.urls import reverse_lazy, reverse
from django.utils.text import capfirst
from django.utils.translation import gettext, gettext_lazy as _
from django.views.generic.list import ListView
from django.views.generic.edit import FormMixin
from django.views.generic.detail import DetailView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import UserPassesTestMixin
from django.utils.decorators import method_decorator
from django.shortcuts import redirect, get_object_or_404,render
from django.contrib import messages
from django.views import View

from surveys.models import Survey, UserAnswer, Question, TYPE_FIELD, ConsentFormContent
from surveys.forms import CreateSurveyForm, EditSurveyForm
from surveys.mixin import ContextTitleMixin
from surveys import app_settings
from surveys.utils import NewPaginator


class SurveyListView(ContextTitleMixin, UserPassesTestMixin, ListView):
    model = Survey
    title_page = 'Survey List'
    paginate_by = app_settings.SURVEY_PAGINATION_NUMBER['survey_list']
    paginator_class = NewPaginator

    def test_func(self):
        return app_settings.SURVEY_ANONYMOUS_VIEW_LIST or self.request.user.is_authenticated

    def get_queryset(self):
        filter = {}
        if app_settings.SURVEY_ANONYMOUS_VIEW_LIST and not self.request.user.is_authenticated:
            filter["can_anonymous_user"] = True
        query = self.request.GET.get('q')
        if query:
            object_list = self.model.objects.filter(name__icontains=query, **filter)
        else:
            object_list = self.model.objects.filter(**filter)
        return object_list

    def get_context_data(self, **kwargs):
        page_number = self.request.GET.get('page', 1)
        context = super().get_context_data(**kwargs)
        page_range = context['page_obj'].paginator.get_elided_page_range(number=page_number)
        context['page_range'] = page_range
        return context


class SurveyFormView(FormMixin, DetailView):
    template_name = 'surveys/form.html'
    success_url = reverse_lazy("surveys:index")

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)

        # use url/get parameters as initial parameters
        if 'create' in request.path:
            questions = Question.objects.filter(survey=self.object)
            for param in request.GET.keys():  # loop over all GET parameters
                for question in questions:
                    if question.key == param:  # find corresponding question
                        field_key = f"field_survey_{question.id}"
                        if field_key in context["form"].field_names:
                            if question.type_field == TYPE_FIELD.rating:
                                if not question.choices:
                                    question.choices = 5
                                context["form"][field_key].field.initial = max(0, min(int(request.GET[param]),
                                                                                      int(question.choices) - 1))
                            elif question.type_field == TYPE_FIELD.multi_select:
                                context["form"][field_key].field.initial = request.GET[param].split(',')
                            else:
                                context["form"][field_key].field.initial = request.GET[param]
                        break

        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        self.object = self.get_object()
        if form.is_valid():
            form.save()
            messages.success(self.request, gettext("%(page_action_name)s succeeded.") % dict(
                page_action_name=capfirst(self.title_page.lower())))
            return self.form_valid(form)
        else:
            messages.error(self.request, gettext("Something went wrong."))
            return self.form_invalid(form)


class ConsentFormView(View):
    template_name = "surveys/consent_form.html"

    def get(self, request, *args, **kwargs):
        survey_slug = kwargs.get("slug")
        survey = get_object_or_404(Survey, slug=survey_slug)

        # Check if the survey has a consent form assigned
        if not survey.consent_form:
            messages.warning(request, _("This survey does not have a consent form."))
            return redirect("surveys:index")

        consent_content = survey.consent_form
        return render(request, self.template_name, {"survey_slug": survey_slug, "consent_content": consent_content})

    def post(self, request, *args, **kwargs):
        survey_slug = kwargs.get("slug")
        if "consent" in request.POST:
            # Store consent acceptance in session
            request.session[f"consent_{survey_slug}"] = True
            return redirect("surveys:create", slug=survey_slug)
        else:
            messages.warning(request, _("You must accept the consent form to proceed."))
            return redirect("surveys:consent", slug=survey_slug)


class CreateSurveyFormView(ContextTitleMixin, SurveyFormView):
    model = Survey
    form_class = CreateSurveyForm
    title_page = _("Add Survey")

    def dispatch(self, request, *args, **kwargs):
        survey = self.get_object()
        survey_slug = survey.slug

        # Check if consent has been accepted
        if not request.session.get(f"consent_{survey_slug}"):
            messages.warning(request, _("You must accept the consent form to proceed."))
            return redirect("surveys:consent", slug=survey_slug)

        # Handle if survey allows anonymous users
        if not request.user.is_authenticated and not survey.can_anonymous_user:
            messages.warning(request, _("Sorry, you must be logged in to fill out the survey."))
            return redirect("surveys:index")

        # Handle if the user has already answered the survey
        if request.user.is_authenticated and not survey.duplicate_entry and \
                UserAnswer.objects.filter(survey=survey, user=request.user).exists():
            messages.warning(request, _("You have already submitted this survey."))
            return redirect("surveys:index")

        return super().dispatch(request, *args, **kwargs)
    
    def get_form(self, form_class=None):
        if form_class is None:
            form_class = self.get_form_class()
        return form_class(survey=self.get_object(), user=self.request.user, **self.get_form_kwargs())

    def get_title_page(self):
        return self.get_object().name

    def get_sub_title_page(self):
        return self.get_object().description

    def get_success_url(self):
        return reverse("surveys:success", kwargs={"slug": self.get_object().slug})


@method_decorator(login_required, name='dispatch')
class EditSurveyFormView(ContextTitleMixin, SurveyFormView):
    form_class = EditSurveyForm
    title_page = "Edit Survey"
    model = UserAnswer

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['object'] = self.get_object().survey
        return context

    def dispatch(self, request, *args, **kwargs):
        # handle if user not same
        user_answer = self.get_object()
        if user_answer.user != request.user or not user_answer.survey.editable:
            messages.warning(request, gettext("You can't edit this survey. You don't have permission."))
            return redirect("surveys:index")
        return super().dispatch(request, *args, **kwargs)

    def get_form(self, form_class=None):
        if form_class is None:
            form_class = self.get_form_class()
        user_answer = self.get_object()
        return form_class(user_answer=user_answer, **self.get_form_kwargs())

    def get_title_page(self):
        return self.get_object().survey.name

    def get_sub_title_page(self):
        return self.get_object().survey.description

    def get_success_url(self):
        return reverse("surveys:success", kwargs={"slug": self.get_object().survey.slug})


@method_decorator(login_required, name='dispatch')
class DeleteSurveyAnswerView(DetailView):
    model = UserAnswer

    def dispatch(self, request, *args, **kwargs):
        # handle if user not same
        user_answer = self.get_object()
        if user_answer.user != request.user or not user_answer.survey.deletable:
            messages.warning(request, gettext("You can't delete this survey. You don't have permission."))
            return redirect("surveys:index")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        user_answer = self.get_object()
        user_answer.delete()
        messages.success(self.request, gettext("Answer succesfully deleted."))
        return redirect("surveys:detail", slug=user_answer.survey.slug)


class DetailSurveyView(ContextTitleMixin, DetailView):
    model = Survey
    template_name = "surveys/answer_list.html"
    title_page = _("Survey Detail")
    paginate_by = app_settings.SURVEY_PAGINATION_NUMBER['answer_list']

    def dispatch(self, request, *args, **kwargs):
        survey = self.get_object()
        if not self.request.user.is_superuser and survey.private_response:
            messages.warning(request, gettext("You can't access this page. You don't have permission."))
            return redirect("surveys:index")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        user_answers = UserAnswer.objects.filter(survey=self.get_object()) \
            .select_related('user').prefetch_related('answer_set__question')
        paginator = NewPaginator(user_answers, self.paginate_by)
        page_number = self.request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
        page_range = paginator.get_elided_page_range(number=page_number)
        context = super().get_context_data(**kwargs)
        context['page_obj'] = page_obj
        context['page_range'] = page_range
        return context


@method_decorator(login_required, name='dispatch')
class DetailResultSurveyView(ContextTitleMixin, DetailView):
    title_page = _("Survey Result")
    template_name = "surveys/detail_result.html"
    model = UserAnswer

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['object'] = self.get_object()
        context['on_detail'] = True
        return context

    def dispatch(self, request, *args, **kwargs):
        # handle if user not same
        user_answer = self.get_object()
        if user_answer.user != request.user:
            messages.warning(request, gettext("You can't access this page. You don't have permission."))
            return redirect("surveys:index")
        return super().dispatch(request, *args, **kwargs)

    def get_title_page(self):
        return self.get_object().survey.name

    def get_sub_title_page(self):
        return self.get_object().survey.description


def share_link(request, slug):
    # this func to handle link redirect to create form or edit form
    survey = get_object_or_404(Survey, slug=slug)
    if request.user.is_authenticated:
        user_answer = UserAnswer.objects.filter(survey=survey, user=request.user).last()
        if user_answer:
            return redirect(reverse_lazy("surveys:edit", kwargs={'pk': user_answer.id}))
    return redirect(reverse_lazy("surveys:create", kwargs={'slug': survey.slug}))


class SuccessPageSurveyView(ContextTitleMixin, DetailView):
    model = Survey
    template_name = "surveys/success-page.html"
    title_page = _("Submitted Successfully")
