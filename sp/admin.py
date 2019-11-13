from __future__ import unicode_literals

from django.contrib import admin

from .models import IdP, IdPAttribute


class IdPAttributeInline(admin.TabularInline):
    model = IdPAttribute
    extra = 0


class IdPAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "slug",
        "last_import",
        "certificate_expires",
        "get_entity_id",
        "get_acs",
        "is_active",
        "last_login",
    )
    list_filter = ("is_active",)
    actions = ("import_metadata", "generate_certificates")
    inlines = (IdPAttributeInline,)
    fieldsets = (
        (None, {"fields": ("name", "slug", "base_url", "notes", "is_active")}),
        (
            "SP Settings",
            {"fields": ("contact_name", "contact_email", "x509_certificate", "private_key", "certificate_expires")},
        ),
        (
            "IdP Metadata",
            {"fields": ("metadata_url", "verify_metadata_cert", "metadata_xml", "lowercase_encoding", "last_import")},
        ),
        ("Logins", {"fields": ("respect_expiration", "login_redirect", "last_login")}),
        ("Advanced", {"classes": ("collapse",), "fields": ("authenticate_method", "login_method")}),
    )
    readonly_fields = ("last_import", "last_login")

    def generate_certificates(self, request, queryset):
        for idp in queryset:
            idp.generate_certificate()

    def import_metadata(self, request, queryset):
        for idp in queryset:
            idp.import_metadata()

    def save_model(self, request, obj, form, change):
        super(IdPAdmin, self).save_model(request, obj, form, change)
        try:
            obj.import_metadata()
        except Exception:
            pass


admin.site.register(IdP, IdPAdmin)
