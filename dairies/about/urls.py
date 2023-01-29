from django.urls import path

from .views import AuthorView

app_name = 'about'

urlpatterns = [
    path('author/', AuthorView.as_view(), name='author'),
]
