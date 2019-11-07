from __future__ import unicode_literals

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from django.db import models
from django.urls import reverse
from django.utils import timezone
from onelogin.saml2.idp_metadata_parser import OneLogin_Saml2_IdPMetadataParser

from urllib.parse import urlparse

import collections
import datetime
import json


class SP(models.Model):
    name = models.CharField(max_length=200)
    slug = models.CharField(max_length=100, unique=True)
    base_url = models.CharField(max_length=200)
    contact_name = models.CharField(max_length=100)
    contact_email = models.CharField(max_length=100)
    x509_certificate = models.TextField(blank=True)
    private_key = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    last_login = models.DateTimeField(null=True, blank=True, default=None)

    class Meta:
        verbose_name = "service provider"

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("sp-metadata", kwargs={"sp_slug": self.slug})

    @property
    def settings(self):
        return {
            "strict": True,
            "sp": {
                "NameIDFormat": "urn:oasis:names:tc:SAML:1.1:nameid-format:unspecified",
                "entityId": self.base_url + self.get_absolute_url(),
                "assertionConsumerService": {
                    "url": self.base_url + reverse("sp-acs", kwargs={"sp_slug": self.slug}),
                    "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST",
                },
                "x509cert": self.x509_certificate,
                "privateKey": self.private_key,
            },
            "contactPerson": {"technical": {"givenName": self.contact_name, "emailAddress": self.contact_email,},},
        }

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
        now = datetime.datetime.utcnow()
        expires = now + datetime.timedelta(days=3650)
        cert = (
            x509.CertificateBuilder()
            .subject_name(name)
            .issuer_name(name)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now)
            .not_valid_after(expires)
            .add_extension(basic_contraints, critical=False)
            .sign(key, hashes.SHA1(), backend)
        )
        self.x509_certificate = cert.public_bytes(serialization.Encoding.PEM).decode("ascii")
        self.save()


class IdP(models.Model):
    sp = models.ForeignKey(SP, related_name="idps", on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    slug = models.CharField(max_length=100)
    metadata_url = models.CharField("Metadata URL", max_length=500, blank=True)
    metadata_xml = models.TextField("Metadata XML", blank=True)
    lowercase_encoding = models.BooleanField(default=False, help_text="Check this if using ADFS.")
    saml_settings = models.TextField(blank=True, help_text="Settings imported and used by the python-saml library.")
    last_import = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    last_login = models.DateTimeField(null=True, blank=True, default=None)

    class Meta:
        verbose_name = "identity provider"
        unique_together = [
            ("sp", "slug"),
        ]

    def __str__(self):
        return "%s (%s)" % (self.name, self.sp)

    def get_absolute_url(self):
        return reverse("sp-idp-login", kwargs={"sp_slug": self.sp.slug, "idp_slug": self.slug})

    def get_test_url(self):
        return reverse("sp-idp-test", kwargs={"sp_slug": self.sp.slug, "idp_slug": self.slug})

    def prepare_request(self, request):
        return {
            "https": "on" if request.is_secure() else "off",
            "http_host": request.get_host(),
            "script_name": request.path_info,
            "server_port": request.get_port(),
            "get_data": request.GET.copy(),
            "post_data": request.POST.copy(),
            "lowercase_urlencoding": self.lowercase_encoding,
        }

    @property
    def settings(self):
        settings_dict = json.loads(self.saml_settings)
        settings_dict.update(self.sp.settings)
        return settings_dict

    def import_metadata(self):
        self.saml_settings = json.dumps(
            OneLogin_Saml2_IdPMetadataParser.parse_remote(self.metadata_url, validate_cert=False)
        )
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


class IdPAttribute(models.Model):
    idp = models.ForeignKey(IdP, related_name="attributes", on_delete=models.CASCADE)
    saml_attribute = models.CharField(max_length=200)
    mapped_name = models.CharField(max_length=200, blank=True)
    is_nameid = models.BooleanField("Is NameID", default=False)

    class Meta:
        verbose_name = "identity provider attribute"
        verbose_name_plural = "identity provider attributes"
        unique_together = [
            ("idp", "saml_attribute"),
        ]

    def __str__(self):
        if self.mapped_name:
            return "{} -> {}".format(self.saml_attribute, self.mapped_name)
        else:
            return "{} (unmapped)".format(self.saml_attribute)
