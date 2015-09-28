#!/usr/bin/env python
from setuptools import setup
import sys

django_version = "django"
if sys.version_info[0] < 3:
    django_version += "<1.7"

setup(
    name="django-arcutils",
    version='1.1.1',
    url='https://github.com/PSU-OIT-ARC/django-arcutils',
    author='PSU - OIT - ARC',
    author_email='consultants@pdx.edu',
    description="ARC Utils for Django sites",
    packages=['arcutils', 'arcutils.templatetags'],
    zip_safe=False,
    classifiers=[
        'Framework :: Django',
    ],
    include_package_data=True,
    install_requires=['stashward'],
    extras_require={
        'ldap': ['ldap3'],
        'test': ['ldap3', 'model_mommy', 'mock', django_version],
    }
)
