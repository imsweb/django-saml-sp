import collections
import datetime
import json
from urllib.parse import urlparse

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.module_loading import import_string
from django.utils.translation import ugettext_lazy as _
from onelogin.saml2.idp_metadata_parser import OneLogin_Saml2_IdPMetadataParser


class IdP(models.Model):
    name = models.CharField(max_length=200)
    slug = models.CharField(max_length=100, unique=True)
    base_url = models.CharField(
        _("Base URL"), max_length=200, help_text=_("Root URL for the site, including http/https, no trailing slash.")
    )
    entity_id = models.CharField(
        _("Entity ID"), max_length=200, blank=True, help_text=_("Leave blank to automatically use the metadata URL.")
    )
    contact_name = models.CharField(max_length=100)
    contact_email = models.EmailField(max_length=100)
    x509_certificate = models.TextField(blank=True)
    private_key = models.TextField(blank=True)
    certificate_expires = models.DateTimeField(null=True, blank=True)
    metadata_url = models.URLField(
        "Metadata URL", max_length=500, blank=True, help_text=_("Leave this blank if entering metadata XML directly.")
    )
    verify_metadata_cert = models.BooleanField(_("Verify metadata URL certificate"), default=True)
    metadata_xml = models.TextField(
        _("Metadata XML"),
        blank=True,
        help_text=_("Automatically loaded from the metadata URL, if specified. Otherwise input directly."),
    )
    lowercase_encoding = models.BooleanField(default=False, help_text=_("Check this if the identity provider is ADFS."))
    saml_settings = models.TextField(
        blank=True, help_text=_("Settings imported and used by the python-saml library."), editable=False
    )
    last_import = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    auth_case_sensitive = models.BooleanField(_("NameID is case sensitive"), default=True)
    create_users = models.BooleanField(_("Create users that do not already exist"), default=True)
    respect_expiration = models.BooleanField(
        _("Respect IdP session expiration"),
        default=False,
        help_text=_(
            "Expires the Django session based on the IdP session expiration. Only works when using SESSION_SERIALIZER=PickleSerializer."
        ),
    )
    login_redirect = models.CharField(
        max_length=200, blank=True, help_text=_("URL name or path to redirect after a successful login.")
    )
    last_login = models.DateTimeField(null=True, blank=True, default=None)
    is_active = models.BooleanField(default=True)
    authenticate_method = models.CharField(max_length=200, default="sp.utils.authenticate")
    login_method = models.CharField(max_length=200, default="sp.utils.login")

    class Meta:
        verbose_name = _("identity provider")

    def __str__(self):
        return self.name

    def get_entity_id(self):
        if self.entity_id:
            return self.entity_id
        else:
            return self.base_url + self.get_absolute_url()

    get_entity_id.short_description = _("Entity ID")

    def get_acs(self):
        return self.base_url + reverse("sp-idp-acs", kwargs={"idp_slug": self.slug})

    get_acs.short_description = _("ACS")

    def get_absolute_url(self):
        return reverse("sp-idp-metadata", kwargs={"idp_slug": self.slug})

    def get_login_url(self):
        return reverse("sp-idp-login", kwargs={"idp_slug": self.slug})

    def get_test_url(self):
        return reverse("sp-idp-test", kwargs={"idp_slug": self.slug})

    def get_verify_url(self):
        return reverse("sp-idp-verify", kwargs={"idp_slug": self.slug})

    def prepare_request(self, request):
        return {
            "https": "on" if request.is_secure() else "off",
            "http_host": request.get_host(),
            "script_name": request.path_info,
            "server_port": 443 if request.is_secure() else request.get_port(),
            "get_data": request.GET.copy(),
            "post_data": request.POST.copy(),
            "lowercase_urlencoding": self.lowercase_encoding,
        }

    @property
    def sp_settings(self):
        return {
            "strict": True,
            "sp": {
                "NameIDFormat": "urn:oasis:names:tc:SAML:1.1:nameid-format:unspecified",
                "entityId": self.get_entity_id(),
                "assertionConsumerService": {
                    "url": self.get_acs(),
                    "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST",
                },
                "x509cert": self.x509_certificate,
                "privateKey": self.private_key,
            },
            "contactPerson": {"technical": {"givenName": self.contact_name, "emailAddress": self.contact_email}},
        }

    @property
    def settings(self):
        settings_dict = json.loads(self.saml_settings)
        settings_dict.update(self.sp_settings)
        return settings_dict

    def generate_certificate(self):
        url_parts = urlparse(self.base_url)
        backend = default_backend()
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048, backend=backend)
        self.private_key = key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode("ascii")
        name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, url_parts.netloc)])
        basic_contraints = x509.BasicConstraints(ca=True, path_length=0)
        now = timezone.now()
        self.certificate_expires = now + datetime.timedelta(days=3650)
        cert = (
            x509.CertificateBuilder()
            .subject_name(name)
            .issuer_name(name)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now)
            .not_valid_after(self.certificate_expires)
            .add_extension(basic_contraints, critical=False)
            .sign(key, hashes.SHA1(), backend)
        )
        self.x509_certificate = cert.public_bytes(serialization.Encoding.PEM).decode("ascii")
        self.save()

    def import_metadata(self):
        if self.metadata_url:
            self.metadata_xml = OneLogin_Saml2_IdPMetadataParser.get_metadata(
                self.metadata_url, validate_cert=self.verify_metadata_cert
            ).decode("utf-8")
        self.saml_settings = json.dumps(OneLogin_Saml2_IdPMetadataParser.parse(self.metadata_xml))
        self.last_import = timezone.now()
        self.save()

    def mapped_attributes(self, saml):
        attrs = collections.OrderedDict()
        for attr in self.attributes.exclude(mapped_name=""):
            value = saml.get_attribute(attr.saml_attribute)
            if value is not None:
                attrs[attr.mapped_name] = value
        return attrs

    def get_nameid(self, saml):
        nameid_attr = self.attributes.filter(is_nameid=True).first()
        if nameid_attr:
            return saml.get_attribute(nameid_attr.saml_attribute)[0]
        else:
            return saml.get_nameid()

    def get_login_redirect(self, redir=None):
        return redir or self.login_redirect or settings.LOGIN_REDIRECT_URL

    def authenticate(self, request, saml):
        return import_string(self.authenticate_method)(request, self, saml)

    def login(self, request, user, saml):
        return import_string(self.login_method)(request, user, self, saml)


class IdPUserDefaultValue(models.Model):
    idp = models.ForeignKey(
        IdP, verbose_name=_("identity provider"), related_name="user_defaults", on_delete=models.CASCADE
    )
    field = models.CharField(max_length=200)
    value = models.TextField()

    class Meta:
        verbose_name = _("user default value")
        verbose_name_plural = _("user default values")
        unique_together = [
            ("idp", "field"),
        ]

    def __str__(self):
        return "{} -> {}".format(self.field, self.value)


class IdPAttribute(models.Model):
    idp = models.ForeignKey(
        IdP, verbose_name=_("identity provider"), related_name="attributes", on_delete=models.CASCADE
    )
    saml_attribute = models.CharField(max_length=200)
    mapped_name = models.CharField(max_length=200, blank=True)
    is_nameid = models.BooleanField(_("Is NameID"), default=False)
    always_update = models.BooleanField(
        _("Always Update"),
        default=False,
        help_text=_(
            "Update this mapped user field on every successful authentication. By default, mapped fields are only set on user creation."
        ),
    )

    class Meta:
        verbose_name = _("attribute mapping")
        verbose_name_plural = _("attribute mappings")
        unique_together = [
            ("idp", "saml_attribute"),
        ]

    def __str__(self):
        if self.mapped_name:
            return "{} -> {}".format(self.saml_attribute, self.mapped_name)
        else:
            return "{} (unmapped)".format(self.saml_attribute)
