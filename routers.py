from django.conf import settings
from django.db import connection
from django_multitenant.utils import get_public_schema_name, app_labels


class TenantSyncRouter(object):
    """
    A router to control which applications will be synced,
    depending if we are syncing the shared apps or the tenant apps.
    """

    @staticmethod
    def allow_migrate(db, app_label, model_name=None, **hints):
        if connection.schema_name == get_public_schema_name():
            if app_label not in app_labels(settings.SHARED_APPS):
                return False
        else:
            if app_label not in app_labels(settings.TENANT_APPS):
                return False

        return None
