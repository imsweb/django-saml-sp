from setuptools import find_packages, setup

app = __import__("sp")

setup(
    name="django-saml-sp",
    version=app.__version__,
    description="A Django application for running one or more SAML service providers (SP).",
    author="Dan Watson",
    author_email="watsond@imsweb.com",
    url="https://github.com/imsweb/django-saml-sp",
    license="BSD",
    packages=find_packages(exclude=["testapp", "testapp.*"]),
    install_requires=["cryptography", "python3-saml",],
    include_package_data=True,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Framework :: Django",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
    ],
    project_urls={"Source": "https://github.com/imsweb/django-saml-sp"},
)
