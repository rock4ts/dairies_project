from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

handler404 = 'core.views.page_not_found'
handler500 = 'core.views.server_error'
handler403 = 'core.views.permission_denied'

urlpatterns = [
    path('dairies/', include('dairies.project-urls')),
]

if settings.DEBUG:
    urlpatterns += (path('__debug__/', include('debug_toolbar.urls'))),
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )
