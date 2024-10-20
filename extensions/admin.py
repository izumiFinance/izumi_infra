# -*- coding: utf-8 -*-
import os
import json
import logging
from datetime import datetime

from django import forms
from django.contrib import admin
from django.contrib.auth.admin import csrf_protect_m
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import path, reverse

from izumi_infra.extensions.conf import extensions_settings
from izumi_infra.extensions.models import CommonSetting
from izumi_infra.utils.APIStatus import CommonStatus
from izumi_infra.utils.admin_utils import NonModelAdmin, readable_size, register, scan_file_tree
from izumi_infra.utils.date_utils import PYTHON_DATETIME_FORMAT
from izumi_infra.utils.exceptions import BizException

logger = logging.getLogger(__name__)


class SystemInvokeForm(forms.Form):
    method = forms.ChoiceField(label="Invoke method",
                               choices=[(m.__name__, m.__name__) for m in extensions_settings.SYSTEM_INVOKE_METHOD_LIST])
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
        invoke_result = None
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
                target = [m for m in  method_list if method == m.__name__]
                if target:
                    func = target[0]
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

@register(CommonSetting)
class CommonSettingAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'key', 'value', 'status', 'value_type', 'update_time')

@register()
class FileBrowserAdmin(NonModelAdmin):
    name = 'File-Browser'
    verbose_name = 'FileBrowser'
    change_list_template = "tools/file_browser.html"


    @csrf_protect_m
    def changelist_view(self, request, extra_context=None):
        context = self.get_extra_context(request)

        try:
            file_list = list(scan_file_tree(extensions_settings.FILE_BROWSER_PATH))
        except Exception as e:
            return HttpResponse("May invalid browser path: " + os.path.abspath(extensions_settings.FILE_BROWSER_PATH))

        item_list = [{"name": f.path[len(extensions_settings.FILE_BROWSER_PATH):],
                      "size": readable_size(f.stat().st_size),
                      "create_time": datetime.strftime(datetime.fromtimestamp(f.stat().st_atime), PYTHON_DATETIME_FORMAT),
                      "update_time": datetime.strftime(datetime.fromtimestamp(f.stat().st_mtime), PYTHON_DATETIME_FORMAT),
                      } for f in file_list]
        item_list.sort(key=lambda f: f['update_time'], reverse=True)
        context = {**context, 'file_context': item_list, 'store_path': os.path.abspath(extensions_settings.FILE_BROWSER_PATH)}
        return super().changelist_view(request, context)

    @csrf_protect_m
    def process_download(self, request):
        if not request.user or not request.user.is_superuser:
            raise BizException(CommonStatus.PERMISSION_DENY)

        fpath = request.GET.get('fpath')
        fpath_abs = os.path.join(extensions_settings.FILE_BROWSER_PATH, fpath)

        if not fpath or not os.path.exists(fpath_abs):
            return HttpResponse(content=f"File not exist: {fpath}")

        with open(fpath_abs, 'r') as f:
            file_data = f.read()
            response = HttpResponse(file_data, content_type="application/octet-stream")
            response["Content-Disposition"] = f"attachment; filename={os.path.basename(fpath)}"
            return response

        return HttpResponse(content="Download file error")

    @csrf_protect_m
    def process_upload(self, request):
        if not request.user or not request.user.is_superuser:
            raise BizException(CommonStatus.PERMISSION_DENY)

        if not request.FILES.get('filename'):
            HttpResponse(content="No file upload")

        upload_file = request.FILES.get('filename')
        fpath_abs = os.path.join(extensions_settings.FILE_BROWSER_PATH, upload_file.name)
        if os.path.exists(fpath_abs):
            return HttpResponse(content=f"File already exist: {upload_file.name}")

        with open(fpath_abs, 'wb') as f:
            f.write(upload_file.read())

        return redirect(reverse('admin:extensions_file-browser_changelist'))

    @csrf_protect_m
    def process_delete(self, request):
        if not request.user or not request.user.is_superuser:
            raise BizException(CommonStatus.PERMISSION_DENY)

        fpath = request.GET.get('fpath')
        fpath_abs = os.path.join(extensions_settings.FILE_BROWSER_PATH, fpath)

        if not fpath or not os.path.exists(fpath_abs):
            HttpResponse(content=f"File not exist: {fpath}")

        os.remove(fpath_abs)

        return redirect(reverse('admin:extensions_file-browser_changelist'))

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('download/', self.admin_site.admin_view(self.process_download), name='process-download'),
            path('upload/', self.admin_site.admin_view(self.process_upload), name='process-upload'),
            path('delete/', self.admin_site.admin_view(self.process_delete), name='process-delete'),
        ]
        return custom_urls + urls
