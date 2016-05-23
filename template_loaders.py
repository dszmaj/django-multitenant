from django.conf import settings
from django.core.exceptions import SuspiciousFileOperation
from django.template import TemplateDoesNotExist
from django.template.loaders.base import Loader
from django.utils._os import safe_join
from django.db import connection

from django_multitenant.postgresql_backend.base import FakeTenant


class FilesystemLoader(Loader):
    is_usable = True

    def get_template_sources(self, template_name, template_dirs=None):
        """
        Returns the absolute paths to "template_name", when appended to each
        directory in "template_dirs". Any paths that don't lie inside one of the
        template dirs are excluded from the result set, for security reasons.
        """
        if not connection.tenant or isinstance(connection.tenant, FakeTenant):
            return
        if not template_dirs:
            template_dirs = self.engine.dirs

        for template_dir in template_dirs:
            try:
                yield safe_join(
                    template_dir,
                    connection.tenant.subdomain,
                    connection.domain.name,
                    template_name
                )
            except SuspiciousFileOperation:
                continue

    def load_template_source(self, template_name, template_dirs=None):
        tried = []
        for filepath in self.get_template_sources(template_name, template_dirs):
            try:
                with open(filepath, 'rb') as fp:
                    return fp.read().decode(settings.FILE_CHARSET), filepath
            except IOError:
                tried.append(filepath)
        raise TemplateDoesNotExist(template_name, tried=tried)

    load_template_source.is_usable = True
