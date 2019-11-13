## Local Test Application

### Start the local SimpleSAML IdP

```
docker run -it --rm -p 8080:8080 -p 8443:8443 \
-e SIMPLESAMLPHP_SP_ENTITY_ID=http://localhost:8000/sso/local/ \
-e SIMPLESAMLPHP_SP_ASSERTION_CONSUMER_SERVICE=http://localhost:8000/sso/local/acs/ \
-e SIMPLESAMLPHP_SP_SINGLE_LOGOUT_SERVICE=http://localhost:8000/sso/local/logout/ \
kristophjunge/test-saml-idp
```

### Bootstrap and run the local SP test app

```
python manage.py migrate
python manage.py bootstrap
python manage.py runserver
```

## Integration Guide

### Settings

* `AUTHENTICATION_BACKENDS` - By default the Django authentication system is used to authenticate and log in users. Add `sp.backends.SAMLAuthenticationBackend` to your `AUTHENTICATION_BACKENDS` setting to authenticate using Django's `User` model. The user is looked up using `User.USERNAME_FIELD` matching the SAML `nameid`, and created if it doesn't already exist. See the *Field Mapping* section below for how to map SAML attributes to `User` attributes.
* `LOGIN_REDIRECT_URL` - This is the URL users will be redirected to by default after a successful login (or verification). Optional if you set `IdP.login_redirect` or specify a `next` parameter in your login URL.
* `SESSION_SERIALIZER` - By default, Django uses `django.contrib.sessions.serializers.JSONSerializer`, which does not allow for setting specific expiration dates on sessions. If you want to use the `IdP.respect_expiration` flag to let the IdP dictate when the Django session should expire, you should change this to `django.contrib.sessions.serializers.PickleSerializer`. But if you do not plan on using that feature, leave the default.

### URLs

The application comes with a URLconf that can be included:

```python
path("sso/", include("sp.urls"))
```

Using the `sso` prefix as above, and assuming an IdP slug of `idp`, the following URLs will be available:

URL | Description
--- | -----------
`/sso/idp/` | The entity ID, and metadata URL. Visiting this will produce metadata XML you can give to the IdP administrator.
`/sso/idp/acs/` | The Assertion Consumer Service (ACS). This is what the IdP will POST to upon a successful login.
`/sso/idp/login/` | URL to trigger the login sequence for this IdP. Available programmatically as `idp.get_login_url()`. Takes a `next` parameter to redirect to after login. Also takes a `reauth` parameter to force the IdP to ask for credentials again (also see the verify URL below).
`/sso/idp/test/` | URL to trigger an IdP login and display a test page containing all the SAML attributes passed back. Available programmatically as `idp.get_test_url()`. Does not actually perform a Django user login.
`/sso/idp/verify/` | URL to trigger a verification sequence for this IdP. Available programmatically as `idp.get_verify_url()`. Does not perform a Django user login, but does check that the user authenticated by the IdP matches the current `request.user`.

### Configuring an identity provider (IdP)

1. Create an `IdP` model object, either via the Django admin or programmatically. If you have metadata from your IdP, you can enter the URL or XML now, but it is not required yet.
2. Generate a certificate to use for SAML requests between your SP and this IdP. You may use the built-in admin action for this by going to the Django admin page for Identity Providers, checking the row(s) you want, and selecting "Generate certificates" from the Action dropdown. If you already have a certificate you want to use, you can paste it into the appropriate fields.
3. Give your IdP administrator the Entity ID/Metadata URL and ACS URL, if they need to explicitly allow access or provide you attributes.
4. At this point, if you didn't in step 1, you'll need to enter either the IdP metadata URL, or metadata XML directly. Saving will automatically trigger an import of the IdP metadata, so you should see the Last Import date update if successful. There is also an "Import metadata" admin action to trigger this manually.

Your IdP is now ready for testing. On the admin page for your IdP object, there is a "Test IdP" button in the upper right corner. You can also visit the `/sso/idp/test/` URL manually to initiate a test. A successful test of the IdP will show a page containing the NameID and SAML attributes provided by the IdP.
