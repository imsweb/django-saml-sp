from setuptools import setup

# Note, to build a wheel that does not include testapp (bdist_wheel does not respect find/exclude):
# python setup.py sdist && pip wheel --no-index --no-deps --wheel-dir dist dist/*.tar.gz

setup()
