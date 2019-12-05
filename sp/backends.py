from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.core.exceptions import FieldDoesNotExist

UserModel = get_user_model()


class SAMLAuthenticationBackend(ModelBackend):
    def authenticate(self, request, idp=None, saml=None):
        nameid = idp.get_nameid(saml)
        attrs = idp.mapped_attributes(saml)
        user, created = UserModel._default_manager.get_or_create(**{UserModel.USERNAME_FIELD: nameid})
        update_fields = []
        always_update = idp.attributes.filter(always_update=True).values_list('mapped_name', flat=True)
        if created:
            default_field_values = {default.field: [default.value] for default in idp.user_defaults.all()}
            attrs.update(default_field_values)
        for field, values in attrs.items():
            if created or field in always_update:
                try:
                    f = UserModel._meta.get_field(field)
                    setattr(user, f.name, values[0])
                    update_fields.append(f.name)
                except FieldDoesNotExist:
                    pass
        if update_fields:
            user.save(update_fields=update_fields)
        return user
