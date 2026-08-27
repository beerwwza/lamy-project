import logging

from django.apps import AppConfig

security_logger = logging.getLogger('myapp.security')


class MyappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'myapp'

    def ready(self):
        from django.contrib.auth.signals import user_login_failed

        def _log_failed_login(sender, credentials, request=None, **kwargs):
            username = credentials.get('username', 'unknown')
            ip = request.META.get('REMOTE_ADDR', 'unknown') if request else 'unknown'
            security_logger.warning(
                '[SECURITY] Failed login attempt: username=%s ip=%s', username, ip
            )

        user_login_failed.connect(_log_failed_login, dispatch_uid='myapp_log_failed_login')
