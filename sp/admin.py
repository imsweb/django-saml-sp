from __future__ import unicode_literals

from django.contrib import admin

from .models import SP, IdP, IdPAttribute


class IdPAttributeInline(admin.TabularInline):
    model = IdPAttribute
    extra = 0


class IdPAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "metadata_url", "last_import", "is_active", "last_login")
    list_filter = ("is_active",)
    actions = ("import_metadata",)
    inlines = (IdPAttributeInline,)

    def import_metadata(self, request, queryset):
        for idp in queryset:
            idp.import_metadata()

    def save_model(self, request, obj, form, change):
        super(IdPAdmin, self).save_model(request, obj, form, change)
        try:
            obj.import_metadata()
        except Exception:
            pass


class SPAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "base_url", "contact_name", "contact_email", "is_active", "last_login")
    list_filter = ("is_active",)
    actions = ("generate_certificate",)

    def generate_certificate(self, request, queryset):
        for sp in queryset:
            sp.generate_certificate()


admin.site.register(IdP, IdPAdmin)
admin.site.register(SP, SPAdmin)
