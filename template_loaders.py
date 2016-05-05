from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
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
            try:
                template_dirs = settings.MULTITENANT_TEMPLATE_DIRS
            except AttributeError:
                raise ImproperlyConfigured('To use {0}.{1} you must define the MULTITENANT_TEMPLATE_DIRS'.format(
                    __name__,
                    FilesystemLoader.__name__
                ))
        for template_dir in template_dirs:
            try:
                if '%s' in template_dir:
                    yield safe_join(template_dir % connection.tenant.domain_url, template_name)
                else:
                    yield safe_join(template_dir, connection.tenant.domain_url, template_name)
            except UnicodeDecodeError:
                # The template dir name was a bytestring that wasn't valid UTF-8.
                raise
            except ValueError:
                # The joined path was located outside of this particular
                # template_dir (it might be inside another one, so this isn't
                # fatal).
                pass

    def load_template_source(self, template_name, template_dirs=None):
        tried = []
        for filepath in self.get_template_sources(template_name, template_dirs):
            try:
                with open(filepath, 'rb') as fp:
                    return fp.read().decode(settings.FILE_CHARSET), filepath
            except IOError:
                tried.append(filepath)
        if tried:
            error_msg = "Tried %s" % tried
        else:
            error_msg = "Your TEMPLATE_DIRS setting is empty. Change it to point to at least one template directory."
        raise TemplateDoesNotExist(error_msg)
    load_template_source.is_usable = True
