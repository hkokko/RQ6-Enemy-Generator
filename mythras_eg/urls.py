import os

from django.conf.urls import include
from django.urls import re_path as url
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from enemygen.reg_views import MyRegistrationView

admin.autodiscover()

# Serve /temp/ from settings.TEMP (where PNG/PDF artifacts are written). Fallback to PROJECT_ROOT/temp.
temp_root = getattr(settings, 'TEMP', os.path.join(settings.PROJECT_ROOT, 'temp'))
# Expose this value so views can reference the exact directory being served at /temp/
setattr(settings, 'TEMP_URL_DOCUMENT_ROOT', temp_root)
# Also expose the URL prefix used to serve temp files (default '/temp/')
setattr(settings, 'TEMP_URL_PREFIX', getattr(settings, 'TEMP_URL_PREFIX', '/temp/'))
# Debug: log the document_root used to serve /temp/
try:
    print('[urls] /temp/ document_root =', temp_root)
    print('[urls] /temp/ url_prefix =', getattr(settings, 'TEMP_URL_PREFIX', '/temp/'))
except Exception:
    pass
temp_path = static(getattr(settings, 'TEMP_URL_PREFIX', '/temp/'), document_root=temp_root)

# DEV-ONLY: serve the temp files via Django
# (Put this unconditionally while debugging; later you can guard with settings.DEBUG)

urlpatterns += [
    re_path(r"^temp/(?P<path>.*)$",
            static_serve,
            {"document_root": str(settings.TEMP_URL_DOCUMENT_ROOT)}),
]

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^accounts/register/$', MyRegistrationView.as_view(), name='registration_register'),

      url(r'^accounts/password/reset/$', auth_views.PasswordResetView.as_view(), name='password_reset'),
      url(r'^accounts/password/reset/done/$', auth_views.PasswordChangeDoneView.as_view(), name='password_reset_done'),
      url(r'^accounts/password/reset/complete/$', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
      url(r'^accounts/password/reset/confirm/(?P<uidb64>[0-9A-Za-z]+)-(?P<token>.+)/$',
                    auth_views.PasswordResetConfirmView.as_view(),
                    name='password_reset_confirm'),


    url(r'^accounts/', include('django_registration.backends.activation.urls')),
    url(r'^accounts/', include('django.contrib.auth.urls')),
    url(r'^', include('enemygen.urls')),
] + temp_path
