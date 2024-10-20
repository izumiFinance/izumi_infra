# -*- coding: utf-8 -*-
import json
import logging
import os

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import csrf_protect_m
from django.forms.forms import MediaDefiningClass
from django.utils.safestring import mark_safe
from izumi_infra.extensions.conf import extensions_settings

from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import JsonLexer

logger = logging.getLogger(__name__)


def json_prettify_styles():
    """
    Used to generate Pygment styles (to be included in a .CSS file) as follows:
        print(json_prettify_styles())
    """
    formatter = HtmlFormatter(style='colorful')
    return formatter.get_style_defs()


def json_prettify(json_data):
    """
    Adapted from:
    https://www.pydanny.com/pretty-formatting-json-django-admin.html
    """

    # Get the Pygments formatter
    formatter = HtmlFormatter(style='colorful')

    # Highlight the data
    json_text = highlight(
        json.dumps(json_data, sort_keys=True, indent=2),
        JsonLexer(),
        formatter
    )

    # Get the stylesheet
    style = "<style>" + formatter.get_style_defs() + "</style>"

    # Safe the output
    return mark_safe(style + json_text)

class FakeModelClass(MediaDefiningClass):
    @property
    def model(cls):
        User = get_user_model()
        attrs = {
            "__module__": cls.__module__,
            "Meta": type(
                "Meta", (), {"proxy": True, "verbose_name": cls.get_verbose_name(), "verbose_name_plural": cls.get_verbose_name()}
            ),
        }
        return type(f"{cls.get_name()}", (User,), attrs)  # noqa


class NonModelAdmin(admin.ModelAdmin, metaclass=FakeModelClass):
    """
    https://github.com/pawnhearts/django_nonmodel_admin
    """
    name = None
    verbose_name = None
    change_list_template = "admin/test.html"

    def get_model_perms(self, request):
        return {"view": True}

    @classmethod
    def get_name(cls):
        return cls.name or cls.__name__.replace("Admin", "")

    @classmethod
    def get_verbose_name(cls):
        return cls.verbose_name or cls.get_name()

    @csrf_protect_m
    def changelist_view(self, request, extra_context=None):
        context = self.get_extra_context(request)
        if extra_context:
            context.update(extra_context)
        return super().changelist_view(request, context)

    def get_extra_context(self, request):
        return {"title": self.get_verbose_name()}

    def get_urls(self):
        # we only need changelist url get page, add url to post data
        return super().get_urls()[:2]

    @csrf_protect_m
    def add_view(self, request, form_url='', extra_context=None):
        logger.warning('nothing impl for add_view')
        return self.changelist_view(request, extra_context)

    @classmethod
    def register(cls, site):
        site.register(cls.model, cls)


def register(*models, site=None):
    """
    Register the given model(s) classes and wrapped ModelAdmin class with
    admin site:
    @register(Author)
    class AuthorAdmin(admin.ModelAdmin):
        pass
    NonModelAdmin classes can be registered without models provided.
    @register()
    class DashboardAdmin(NonModelAdmin):
        name = 'dashboard'
        verbose_name = 'My dashboard'
        change_list_template = "my_app/dashboard.html"
    The `site` kwarg is an admin site to use instead of the default admin site.
    """
    from django.contrib.admin import ModelAdmin
    from django.contrib.admin.sites import AdminSite
    from django.contrib.admin.sites import site as default_site

    def _model_admin_wrapper(admin_class):
        nonlocal models
        if not models:
            if hasattr(admin_class, 'model'):
                models = (admin_class.model,)
            else:
                raise ValueError('At least one model must be passed to register.')

        admin_site = site or default_site

        if not isinstance(admin_site, AdminSite):
            raise ValueError('site must subclass AdminSite')

        if not issubclass(admin_class, ModelAdmin):
            raise ValueError('Wrapped class must subclass ModelAdmin.')

        admin_site.register(models, admin_class=admin_class)

        return admin_class

    return _model_admin_wrapper


try:
    from os import scandir
except ImportError:
    from scandir import scandir

def scan_file_tree(path):
    """Recursively yield DirEntry objects for given directory."""
    for entry in scandir(path):
        if entry.is_dir(follow_symlinks=False):
            yield from scan_file_tree(entry.path)
        else:
            yield entry

def readable_size(size, precision=2):
    suffixes=['B','KB','MB','GB','TB']
    suffixIndex = 0
    while size >= 1024 and len(suffixes):
        suffixIndex += 1
        size = size/1024.0
    return "%.*f%s"%(precision, size, suffixes[suffixIndex])

def save_content_to_store(filename: str, content: str) -> str:
    fpath = os.path.join(extensions_settings.FILE_BROWSER_PATH, filename)
    with open(fpath, 'w+') as f:
        f.write(content)

    return fpath
