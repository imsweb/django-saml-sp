## 0.7.0

* Updated certificate signing algorithm to SHA256 (#23).
* Refactored usage of `RelayState` to not do unnecessary signing. This parameter is limited to 80 characters, almost all of which were being taken by the signature and timestamp, leaving very little room for redirect URLs.


## 0.6.1

* Fix an issue with migrations on Oracle (#21).


## 0.6.0

* Allow customization of `prepare_request` via a new `SP_PREPARE_REQUEST` setting, and a new `IdP.prepare_request_method` field.
* Allow customization of how users are created and updated via a new `SP_UPDATE_USER` setting, and a new `IdP.update_user_method` field. Also make `SAMLAuthenticationBackend` more subclassing-friendly by having an `update_user` method available to override.
* Support IdP-based session expiration with `JSONSerializer` when using Django 4.1 or later.


## 0.5.0

* Removed `IdP.slug` in favor of an `IdP.url_params` JSON field containing the URL parameters that uniquely identify a configured IdP. Since unique JSON fields are not supported on all databases, you should ensure the the parameters are unique in your application.
* Added an `SP_LOGOUT` setting, as well as `IdP.logout_method` and `IdP.logout_redirect` model fields to customize the logout process.
* Support single logout (SLO), along with a new `IdP.logout_triggers_slo` to determine if a site logout should trigger an IdP SLO.

**Upgrading from 0.4 [BREAKING]**: You will need to change your included URLs to have an `<idp_slug>` path parameter. For instance, `path("sso/", include("sp.urls"))` becomes `path("sso/<idp_slug>/", include("sp.urls"))`. Going forward, you can use whatever path prefixes you like, named however you want. This is just for migrating existing IdPs.
