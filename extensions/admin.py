# -*- coding: utf-8 -*-
import json
import logging
from datetime import datetime
from importlib import import_module

from django import forms
from django.contrib import admin
from django.contrib.auth.admin import csrf_protect_m

from izumi_infra.extensions.conf import extensions_settings
from izumi_infra.utils.APIStatus import CommonStatus
from izumi_infra.utils.admin_utils import NonModelAdmin, register
from izumi_infra.utils.date_utils import PYTHON_DATETIME_FORMAT
from izumi_infra.utils.exceptions import BizException

logger = logging.getLogger(__name__)


class SystemInvokeForm(forms.Form):
    method = forms.ChoiceField(label="Invoke method",
                               choices=[(m[1], m[1]) for m in extensions_settings.SYSTEM_INVOKE_METHOD_LIST])
    data = forms.JSONField(label='Invoke data')


@register()
class SystemInvokeAdmin(NonModelAdmin):
    name = 'System-Invoke'
    verbose_name = 'SystemInvoke'
    change_list_template = "tools/sys_invoke.html"

    def get_extra_context(self, request):
        super_context = super().get_extra_context(request)
        ctx = {
            'form': SystemInvokeForm(),
        }
        return { **super_context, **ctx }

    @csrf_protect_m
    def add_view(self, request, form_url='', extra_context=None):
        if not request.user or not request.user.is_superuser:
            raise BizException(CommonStatus.PERMISSION_DENY)

        post_data = dict(request.POST)
        post_data.pop('csrfmiddlewaretoken')
        post_data['time'] = datetime.strftime(datetime.now(), PYTHON_DATETIME_FORMAT)
        errors = []

        method = None
        data = None
        # TODO better form validate
        if not post_data.get('method'):
            errors.append('method required')
        else:
            method = post_data.get('method')[0]

        if not post_data.get('data'):
            errors.append('data required')
        else:
            try:
                data = json.loads(post_data.get('data')[0])
            except Exception as e:
                errors.append('data is invalid json')

        if method:
            method_list = extensions_settings.SYSTEM_INVOKE_METHOD_LIST
            try:
                target = [m for m in  method_list if method == m[1]]
                if target:
                    target_first = target[0]
                    module = import_module(target_first[0])
                    func = getattr(module, target_first[1])
                    if data:
                        invoke_result = func(data)
                    else:
                        invoke_result = func()
                else:
                    errors.append(f'no match target for: {method}, conf: {method_list}')
            except Exception as e:
                logger.error(e)
                errors.append(str(e))

        if not invoke_result: invoke_result = 'Success invoke'
        if errors: invoke_result = ', '.join(errors)
        return super().changelist_view(request, { 'result': invoke_result, 'post_data': post_data })
