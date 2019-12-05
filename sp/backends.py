from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.core.exceptions import FieldDoesNotExist

UserModel = get_user_model()


class SAMLAuthenticationBackend(ModelBackend):
    def authenticate(self, request, idp=None, saml=None):
        nameid = idp.get_nameid(saml)
        attrs = idp.mapped_attributes(saml)
        nameid_lookup = UserModel.USERNAME_FIELD
        if not idp.auth_case_sensitive:
            nameid_lookup += "__iexact"

        try:
            user = UserModel._default_manager.get(**{nameid_lookup: nameid})
            created = False
        except UserModel.DoesNotExist:
            if idp.create_users:
                user = UserModel(**{UserModel.USERNAME_FIELD: nameid})
                user.set_unusable_password()
                created = True
            else:
                return None
        except UserModel.MultipleObjectsReturned:
            return None

        # The set of mapped attributes that should always be updated on the user.
        always_update = set(idp.attributes.filter(always_update=True).values_list("mapped_name", flat=True))

        # For users created by this backend, set initial user default values.
        if created:
            attrs.update({default.field: [default.value] for default in idp.user_defaults.all()})

        # Keep track of which fields (if any) were updated.
        update_fields = []
        for field, values in attrs.items():
            if created or field in always_update:
                try:
                    f = UserModel._meta.get_field(field)
                    # Only update if the field changed. This is a primitive check, but will catch most cases.
                    if values[0] != getattr(user, f.attname):
                        setattr(user, f.attname, values[0])
                        update_fields.append(f.name)
                except FieldDoesNotExist:
                    pass

        if created or update_fields:
            # Doing a full clean will make sure the values we set are of the correct types before saving.
            user.full_clean(validate_unique=False)
            if created:
                user.save()
            else:
                user.save(update_fields=update_fields)

        return user
