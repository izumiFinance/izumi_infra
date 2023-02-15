# -*- coding: utf-8 -*-
from logging import LogRecord, StreamHandler

from izumi_infra.extensions.tasks import send_email_to_superuser_task

class AsyncEmailAlertLogHandler(StreamHandler):
    def __init__(self, include_html=False):
        super().__init__()

    def emit(self, record: LogRecord) -> None:
        # super().emit(record)
        msg_subject = f'[System Alert] [{record.asctime}] - {record.message[:30]}'
        msg_body = self.formatter.format(record)
        send_email_to_superuser_task.delay(msg_subject, msg_body)
