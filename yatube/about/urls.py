from django.urls import path

from .views import AuthorView, TechsView

app_name = 'about'

urlpatterns = [
    path('author/', AuthorView.as_view(), name='author'),
    path('tech/', TechsView.as_view(), name='tech'),
]
