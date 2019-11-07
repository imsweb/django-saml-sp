from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from sp.models import SP


class Command(BaseCommand):
    help = 'Bootstraps the SP with a default "admin" user'

    def handle(self, *args, **options):
        User = get_user_model()
        if User.objects.count() == 0:
            print('Creating default "admin" account with password "letmein" -- change this immediately!')
            User.objects.create_superuser("admin", "admin@example.com", "letmein", first_name="Admin", last_name="User")
        if SP.objects.count() == 0:
            print('Creating "default" SP for http://localhost:8000')
            sp = SP.objects.create(
                name="Default Service Provider",
                slug="default",
                base_url="http://localhost:8000",
                contact_name="Admin User",
                contact_email="admin@example.com",
            )
            sp.generate_certificate()
            print('Creating "local" IdP at http://localhost:8080/simplesaml/saml2/idp/metadata.php')
            idp = sp.idps.create(
                name="Local", slug="local", metadata_url="http://localhost:8080/simplesaml/saml2/idp/metadata.php",
            )
            # The local IdP sends an email address, but it isn't the nameid. Override it to be our nameid, AND set the
            # email field on User.
            idp.attributes.create(saml_attribute="email", mapped_name="email", is_nameid=True)
            try:
                idp.import_metadata()
            except Exception:
                print("Could not import IdP metadata; make sure your local IdP exposes {}".format(idp.metadata_url))
