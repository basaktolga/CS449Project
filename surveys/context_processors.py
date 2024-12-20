from surveys import app_settings
from surveys.utils import get_type_field


def surveys_context(request):
    context = {
        'get_master_template': app_settings.SURVEY_MASTER_TEMPLATE,
        'chart_js_src': app_settings.CHART_JS_SRC,
        'get_type_field': get_type_field,
        'link_back_on_success_page': app_settings.SURVEY_LINK_BACK_ON_SUCCESS_PAGE
    }
    return context
