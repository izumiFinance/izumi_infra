# -*- coding: utf-8 -*-
import logging
from typing import List
from celery.app import shared_task
from django.core.mail import send_mail
from cachetools import TTLCache, cached
from django.conf import settings

from izumi_infra.extensions.conf import extensions_settings

logger = logging.getLogger(__name__)

@shared_task()
def send_email_to_superuser_task(subject: str, message: str) -> None:
    try:
        superuser_emails = get_superuser_email_list()
        admin_emails = get_admins_email_list()
        target_emails = [*superuser_emails, *admin_emails]
        if not target_emails:
            logger.warn('miss superuser of email for sending')
            return

        from_email_addr_list = [
            extensions_settings.ALERT_FROM_EMAIL,
            settings.SERVER_EMAIL,
            settings.DEFAULT_FROM_EMAIL,
            'alert@notifications.izumi.finance'
        ]
        from_email_addr = next(addr for addr in from_email_addr_list if addr)

        send_mail(
            subject,
            message,
            from_email_addr,
            target_emails,
            fail_silently=False,
        )
    except Exception as e:
        logger.exception(e)

@cached(cache=TTLCache(maxsize=1, ttl=5 * 60))
def get_superuser_email_list():
    from django.contrib.auth.models import User
    superUsers: List[str] = User.objects.exclude(email__isnull=True).exclude(
        email__exact='').filter(is_superuser=True).values_list('email', flat=True)
    return list(superUsers)

def get_admins_email_list():
    # like: from django.utils.log import AdminEmailHandler
    # see https://docs.djangoproject.com/en/4.1/ref/settings/#admins
    if settings.ADMINS:
        return [admin[1] for admin in settings.ADMINS]
    else:
        return []
