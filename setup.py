import sys

from setuptools import find_packages, setup


with open('VERSION') as version_fp:
    VERSION = version_fp.read().strip()


# Base dependencies
install_requires = [
    'certifi>=2017.7.27.1',
    'django-local-settings>=1.0b7',
    'pytz>=2017.2',
    'raven>=6.1.0',
]

if sys.version_info[:2] < (3, 4):
    django_version = '1.8'
    install_requires.append('enum34')
else:
    django_version = '1.11'

# Dependencies that are used in multiple places
deps = {
    'coverage': 'coverage>=4.4.1',
    'djangorestframework': 'djangorestframework>=3.6.3',
    'ldap3': 'ldap3>=2.3',
}

setup(
    name='django-arcutils',
    version=VERSION,
    url='https://github.com/PSU-OIT-ARC/django-arcutils',
    author='PSU - OIT - WDT',
    author_email='webteam@pdx.edu',
    description='Common utilities used in WDT Django projects',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=install_requires,
    extras_require={
        'ldap': [
            deps['ldap3'],
        ],
        'dev': [
            deps['coverage'],
            'django>={django_version},<{django_version}.999'.format_map(locals()),
            deps['djangorestframework'],
            'flake8',
            deps['ldap3'],
            'psu.oit.arc.tasks',
            'tox>=2.7.0',
        ],
        'tox': [
            deps['coverage'],
            deps['djangorestframework'],
            'flake8',
            deps['ldap3'],
            'psu.oit.arc.tasks',
        ]
    },
    entry_points="""
    [console_scripts]
    arcutils = arcutils.__main__:main

    """,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Framework :: Django',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
)
