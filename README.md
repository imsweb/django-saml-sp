## Test Application

```
docker run -it --rm -p 8080:8080 -p 8443:8443 \
-e SIMPLESAMLPHP_SP_ENTITY_ID=http://localhost:8000/sso/metadata/default/ \
-e SIMPLESAMLPHP_SP_ASSERTION_CONSUMER_SERVICE=http://localhost:8000/sso/acs/default/ \
-e SIMPLESAMLPHP_SP_SINGLE_LOGOUT_SERVICE=http://localhost:8000/sso/logout/default/ \
kristophjunge/test-saml-idp
```

```
python manage.py migrate
python manage.py bootstrap
python manage.py runserver
```
