#!/usr/bin/env python
from setuptools import setup

setup(
    name="django-arcutils",
    version='0.0.1',
    url='https://github.com/PSU-OIT-ARC/django-arcutils',
    author='Matt Johnson',
    author_email='mdj2@pdx.edu',
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
        'test': ['ldap3', 'model_mommy', 'mock', 'django'],
    }
)
