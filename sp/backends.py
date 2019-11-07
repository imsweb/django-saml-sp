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
        for field, values in attrs.items():
            try:
                f = UserModel._meta.get_field(field)
                setattr(user, f.name, values[0])
                update_fields.append(f.name)
            except FieldDoesNotExist:
                pass
        if update_fields:
            user.save(update_fields=update_fields)
        return user
