from setuptools import find_packages, setup


setup(
    name="django-saml-sp",
    version="0.0.1",
    description="A Django application for running a SAML SP.",
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
    ],
)
