import tldextract

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import DisallowedHost
from django.db import connection
from django.http import Http404
from django_multitenant.utils import get_tenant_model, get_domain_model


class TenantMiddleware(object):
    """
    This middleware should be placed at the very top of the middleware stack.
    Selects the proper database schema using the request host. Can fail in
    various ways which is better than corrupting or revealing data.
    """
    DOMAIN_NOT_FOUND_EXCEPTION = Http404

    def process_request(self, request):
        # Connection needs first to be at the public schema, as this is where
        # the tenant metadata is stored.
        connection.set_schema_to_public()

        extract = tldextract.extract(request.get_host())
        domain = ''.join([extract.domain, extract.suffix])

        subdomain = extract.subdomain if extract.subdomain is not 'www' else False
        request.subdomain = subdomain or None

        DomainModel = get_domain_model()

        try:
            request.domain = DomainModel.objects.get(name=domain)
            request.tenant = request.domain.owner
            connection.set_tenant(request.tenant)
        except DomainModel.DoesNotExist:
            raise self.DOMAIN_NOT_FOUND_EXCEPTION(
                'No domain "{}" set in the system'.format(domain)
            )

        # Content type can no longer be cached as public and tenant schemas
        # have different models. If someone wants to change this, the cache
        # needs to be separated between public and shared schemas. If this
        # cache isn't cleared, this can cause permission problems. For example,
        # on public, a particular model has id 14, but on the tenants it has
        # the id 15. if 14 is cached instead of 15, the permissions for the
        # wrong model will be fetched.
        ContentType.objects.clear_cache()
