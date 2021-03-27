## Installation

* `pip install django-saml-sp`
* Add `sp` to your `INSTALLED_APPS` setting

## Local Test Application

### Start the local SimpleSAML IdP

```
docker run -it --rm -p 8080:8080 -p 8443:8443 \
-e SIMPLESAMLPHP_SP_ENTITY_ID=http://localhost:8000/sso/local/ \
-e SIMPLESAMLPHP_SP_ASSERTION_CONSUMER_SERVICE=http://localhost:8000/sso/local/acs/ \
-e SIMPLESAMLPHP_SP_SINGLE_LOGOUT_SERVICE=http://localhost:8000/sso/local/slo/ \
kristophjunge/test-saml-idp
```

### Bootstrap and run the local SP test app

```
python manage.py migrate
python manage.py bootstrap
python manage.py runserver
```

The test SAML IdP defines the following user accounts you can use for testing:

| UID | Username | Password | Group | Email |
|---|---|---|---|---|
| 1 | user1 | user1pass | group1 | user1@example.com |
| 2 | user2 | user2pass | group2 | user2@example.com |


## Integration Guide

### Django Settings

* `AUTHENTICATION_BACKENDS` - By default the Django authentication system is used to authenticate and log in users. Add `sp.backends.SAMLAuthenticationBackend` to your `AUTHENTICATION_BACKENDS` setting to authenticate using Django's `User` model. The user is looked up using `User.USERNAME_FIELD` matching the SAML `nameid`, and optionally created if it doesn't already exist. See the *Field Mapping* section below for how to map SAML attributes to `User` attributes.
* `LOGIN_REDIRECT_URL` - This is the URL users will be redirected to by default after a successful login (or verification). Optional if you set `IdP.login_redirect` or specify a `next` parameter in your login URL.
* `LOGOUT_REDIRECT_URL` - This is the URL users will be redirected to by default after a successful logout. Optional if you set `IdP.logout_redirect` or specify a `next` parameter in your logout URL.
* `SESSION_SERIALIZER` - By default, Django uses `django.contrib.sessions.serializers.JSONSerializer`, which does not allow for setting specific expiration dates on sessions. If you want to use the `IdP.respect_expiration` flag to let the IdP dictate when the Django session should expire, you should change this to `django.contrib.sessions.serializers.PickleSerializer`. But if you do not plan on using that feature, leave the default.

### SP Settings

* `SP_IDP_LOADER` - Allow you to specify a custom method for the SP views to retrieve an `IdP` instance given a request and the URL path parameters.
* `SP_AUTHENTICATE` - A custom authentication method to use for `IdP` instances that do not specify one. By default, `sp.utils.authenticate` is used (delegating to the auth backend).
* `SP_LOGIN` - A custom login method to use for `IdP` instances that do not specify one. By default, `sp.utils.login` is used (again, delegating to the auth backend).
* `SP_LOGOUT` - A custom logout method to use for `IdP` instances that do not specify one. By default, `sp.utils.logout` is used, which simply delegates to Django's `auth.logout`.
* `SP_UNIQUE_USERNAMES` - When `True` (the default), `SAMLAuthenticationBackend` will generate usernames unique to the `IdP` that authenticated them, both when associating existing users and creating new users. This prevents user accounts from being linked to multiple IDPs (and prevents spoofing if untrusted IDPs can be configured).

### URLs

The application comes with a URLconf that can be included, using any path parameters you want. The `IdP` is fetched by matching any URL parameters to the `url_params` field (or by some custom means via `SP_IDP_LOADER` above). For example:

```python
path("<prefix>/sso/<idp_slug>/", include("sp.urls"))
```

Assuming the URL configuration above, and an `IdP` configured with `url_params={"prefix": "my", "idp_slug": "local"}`, the following URLs would be available:

URL | Description
--- | -----------
`/my/sso/local/` | The entity ID, and metadata URL. Visiting this will produce metadata XML you can give to the IdP administrator.
`/my/sso/local/acs/` | The Assertion Consumer Service (ACS). This is what the IdP will POST to upon a successful login.
`/my/sso/local/slo/` | The Single Logout Service (SLO). The IdP will redirect to this URL when logging out of all SSO services.
`/my/sso/local/login/` | URL to trigger the login sequence for this IdP. Available programmatically as `idp.get_login_url()`. Takes a `next` parameter to redirect to after login. Also takes a `reauth` parameter to force the IdP to ask for credentials again (also see the verify URL below).
`/my/sso/local/test/` | URL to trigger an IdP login and display a test page containing all the SAML attributes passed back. Available programmatically as `idp.get_test_url()`. Does not actually perform a Django user login.
`/my/sso/local/verify/` | URL to trigger a verification sequence for this IdP. Available programmatically as `idp.get_verify_url()`. Does not perform a Django user login, but does check that the user authenticated by the IdP matches the current `request.user`.
`/my/sso/local/logout/` | URL to trigger the logout sequence for this IdP. Available programmatically as `idp.get_logout_url()`. Takes a `next` parameter to redirect to after logout.

You can also include `sp.urls` without any URL parameters (e.g. `path("sso/", include("sp.urls"))`) if only a single `IdP` is needed (it should have `url_params={}`).


### Configuring an identity provider (IdP)

1. Create an `IdP` model object, either via the Django admin or programmatically. If you have metadata from your IdP, you can enter the URL or XML now, but it is not required yet.
2. Generate a certificate to use for SAML requests between your SP and this IdP. You may use the built-in admin action for this by going to the Django admin page for Identity Providers, checking the row(s) you want, and selecting "Generate certificates" from the Action dropdown. If you already have a certificate you want to use, you can paste it into the appropriate fields.
3. Give your IdP administrator the Entity ID/Metadata URL and ACS URL, if they need to explicitly allow access or provide you attributes.
4. At this point, if you didn't in step 1, you'll need to enter either the IdP metadata URL, or metadata XML directly. Saving will automatically trigger an import of the IdP metadata, so you should see the Last Import date update if successful. There is also an "Import metadata" admin action to trigger this manually.

Your IdP is now ready for testing. On the admin page for your IdP object, there is a "Test IdP" button in the upper right corner. You can also visit the `.../test/` URL (see above) manually to initiate a test. A successful test of the IdP will show a page containing the NameID and SAML attributes provided by the IdP.
