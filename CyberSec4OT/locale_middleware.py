from django.utils import translation
from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse

class LocaleMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if there's a language parameter in the URL
        lang = request.GET.get('lang')
        if lang and lang in [code for code, name in settings.LANGUAGES]:
            # Set the language in the session
            request.session[settings.LANGUAGE_SESSION_KEY] = lang
            translation.activate(lang)
            response = redirect(request.path)
            response.set_cookie(settings.LANGUAGE_COOKIE_NAME, lang)
            return response

        # Get language from session or cookie or default
        lang_code = (
            request.session.get(settings.LANGUAGE_SESSION_KEY)
            or request.COOKIES.get(settings.LANGUAGE_COOKIE_NAME)
            or settings.LANGUAGE_CODE
        )
        translation.activate(lang_code)
        request.LANGUAGE_CODE = lang_code

        response = self.get_response(request)
        response.set_cookie(settings.LANGUAGE_COOKIE_NAME, lang_code)
        return response

    def process_response(self, request, response):
        lang_code = translation.get_language()
        response.set_cookie(settings.LANGUAGE_COOKIE_NAME, lang_code)
        return response
