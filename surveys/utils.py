from django.utils.safestring import mark_safe
from django.core.paginator import Paginator
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from surveys import models


def create_star(active_star: int, num_stars: int = 5, id_element: str = '') -> str:
    inactive_star = num_stars - active_star
    elements = [f'<div class="flex content-center" id="parent_start_{id_element}">']
    for _ in range(int(active_star)):
        elements.append('<i class ="rating__star rating_active"> </i>')
    for _ in range(inactive_star):
        elements.append('<i class ="rating__star rating_inactive"> </i>')
    elements.append('</div>')
    return mark_safe(''.join(elements))


class NewPaginator(Paginator):
    # adaptation from new Paginator django >= 3.2 
    # https://docs.djangoproject.com/en/4.0/_modules/django/core/paginator/#Paginator.get_elided_page_range
    # Translators: String used to replace omitted page numbers in elided page
    # range generated by paginators, e.g. [1, 2, '…', 5, 6, 7, '…', 9, 10].
    ELLIPSIS = _("…")

    def get_elided_page_range(self, number=1, *, on_each_side=3, on_ends=1):
        """
        Return a 1-based range of pages with some values elided.

        If the page range is larger than a given size, the whole range is not
        provided and a compact form is returned instead, e.g. for a paginator
        with 50 pages, if page 43 were the current page, the output, with the
        default arguments, would be:

            1, 2, …, 40, 41, 42, 43, 44, 45, 46, …, 49, 50.
        """
        number = self.validate_number(number)

        if self.num_pages <= (on_each_side + on_ends) * 2:
            yield from self.page_range
            return

        if number > (1 + on_each_side + on_ends) + 1:
            yield from range(1, on_ends + 1)
            yield self.ELLIPSIS
            yield from range(number - on_each_side, number + 1)
        else:
            yield from range(1, number + 1)

        if number < (self.num_pages - on_each_side - on_ends) - 1:
            yield from range(number + 1, number + on_each_side + 1)
            yield self.ELLIPSIS
            yield from range(self.num_pages - on_ends + 1, self.num_pages + 1)
        else:
            yield from range(number + 1, self.num_pages + 1)


def get_type_field():
    return [
        {
            'id': models.TYPE_FIELD.text,
            'label': _("Text"),
            'icon': "bi bi-type"
        },
        {
            'id': models.TYPE_FIELD.number,
            'label': _("Number"),
            'icon': "bi bi-123"
        },
        {
            'id': models.TYPE_FIELD.radio,
            'label': _("Radio"),
            'icon': "bi bi-ui-radios"
        },
        {
            'id': models.TYPE_FIELD.select,
            'label': _("Select"),
            'icon': "bi bi-menu-button-wide-fill"
        },
        {
            'id': models.TYPE_FIELD.multi_select,
            'label': _("Multi Select"),
            'icon': "bi bi-ui-checks"
        },
        {
            'id': models.TYPE_FIELD.text_area,
            'label': _("Text Area"),
            'icon': "bi bi-textarea-resize"
        },
        {
            'id': models.TYPE_FIELD.url,
            'label': _("URL"),
            'icon': "bi bi-link"
        },
        {
            'id': models.TYPE_FIELD.email,
            'label': _("Email"),
            'icon': "bi bi-envelope"
        },
        {
            'id': models.TYPE_FIELD.date,
            'label': _("Date"),
            'icon': "bi bi-calendar-event"
        },
        {
            'id': models.TYPE_FIELD.rating,
            'label': _("Rating"),
            'icon': "bi bi-star"
        }
    ]
