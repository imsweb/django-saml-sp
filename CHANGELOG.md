## 0.5.0

* Removed `IdP.slug` in favor of an `IdP.url_params` JSON field containing the URL parameters that uniquely identify a configured IdP. Since unique JSON fields are not supported on all databases, you should ensure the the parameters are unique in your application.
* Added an `SP_LOGOUT` setting, as well as `IdP.logout_method` and `IdP.logout_redirect` model fields to customize the logout process.
* Support single logout (SLO), along with a new `IdP.logout_triggers_slo` to determine if a site logout should trigger an IdP SLO.

**Upgrading from 0.4 [BREAKING]**: You will need to change your included URLs to have an `<idp_slug>` path parameter. For instance, `path("sso/", include("sp.urls"))` becomes `path("sso/<idp_slug>/", include("sp.urls"))`. Going forward, you can use whatever path prefixes you like, named however you want. This is just for migrating existing IdPs.
