# -*- coding: utf-8 -*-
from django.contrib import admin
from django.urls import path, include

from izumi_infra.extensions.form import IzumiAuthenticationForm
from izumi_infra.extensions.conf import extensions_settings

urlpatterns = [
    path('api/v1/captcha/', include('captcha.urls')),
]

# replace login form
admin.autodiscover()
admin.site.site_header = extensions_settings.ADMIN_SITE_NAME
admin.site.login_form = IzumiAuthenticationForm
