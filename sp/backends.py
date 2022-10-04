import re

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

from .models import IdPUser

UserModel = get_user_model()


class SAMLAuthenticationBackend(ModelBackend):
    def get_username(self, idp, saml):
        """
        For users not already associated with the IdP, generate a username to either
        look up and associate, or to use when creating a new User.
        """
        # Start with either the SAML nameid, or SAML attribute mapped to nameid.
        username = idp.get_nameid(saml)
        # Add IdP-specific prefix and suffix.
        username = idp.username_prefix + username + idp.username_suffix
        # Make sure the username is valid for Django's User model.
        username = re.sub(r"[^a-zA-Z0-9_@\+\.]", "-", username)
        # Make the username unique to the IdP, if SP_UNIQUE_USERNAMES is True.
        if getattr(settings, "SP_UNIQUE_USERNAMES", True):
            username += "-" + str(idp.pk)
        return username

    def authenticate(self, request, idp=None, saml=None):
        # The nameid (potentially mapped) to associate a User with an IdP.
        nameid = idp.get_nameid(saml)
        created = False

        try:
            # If this nameid is already associated with a User, our job is done.
            user = idp.users.get(nameid=nameid).user
        except IdPUser.DoesNotExist:
            # Otherwise, associate or create a user with the generated username, if the
            # IdP settings allow it.
            username = self.get_username(idp, saml)
            username_field = UserModel.USERNAME_FIELD
            if not idp.auth_case_sensitive:
                username_field += "__iexact"
            try:
                # If we find an existing User, and the IdP allows it, associate them
                # with this IdP.
                user = UserModel._default_manager.get(**{username_field: username})
                if not idp.associate_users:
                    return None
                idp.users.create(nameid=nameid, user=user)
            except UserModel.DoesNotExist:
                if not idp.create_users:
                    return None
                # Create the User if the IdP allows it.
                user = UserModel(**{UserModel.USERNAME_FIELD: username})
                user.set_unusable_password()
                created = True
            except UserModel.MultipleObjectsReturned:
                # This can happen with case-insensitive auth.
                return None

        user = self.update_user(request, idp, saml, user, created)

        if created:
            idp.users.create(nameid=nameid, user=user)

        return user

    def update_user(self, request, idp, saml, user, created):
        # By default just call through to IdP.update_user, but provide an easy place
        # to customize this behavior for subclasses.
        return idp.update_user(request, saml, user, created)
