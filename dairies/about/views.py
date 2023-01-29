from django.views.generic.base import TemplateView


class AuthorView(TemplateView):
    template_name = 'about/author.html'
