import sys

from setuptools import find_packages, setup


with open('VERSION') as version_fp:
    VERSION = version_fp.read().strip()


# Base dependencies
install_requires = [
    'certifi>=2017.4.17',
    'django-local-settings>=1.0b6',
    'pytz>=2017.2',
    'raven>=6.1.0',
    'stashward',
]

if sys.version_info[:2] < (3, 4):
    django_version = '1.8'
    install_requires.append('enum34')
else:
    django_version = '1.11'

# Dependencies that are used in multiple places
deps = {
    'djangorestframework': 'djangorestframework>=3.6.3',
    'ldap3': 'ldap3>=2.2.4',
}

setup(
    name='django-arcutils',
    version=VERSION,
    url='https://github.com/PSU-OIT-ARC/django-arcutils',
    author='PSU - OIT - ARC',
    author_email='consultants@pdx.edu',
    description='Common utilities used in ARC Django projects',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=install_requires,
    extras_require={
        'ldap': [
            deps['ldap3'],
        ],
        'dev': [
            'django>={django_version},<{django_version}.999'.format_map(locals()),
            deps['djangorestframework'],
            'flake8',
            deps['ldap3'],
            'psu.oit.arc.tasks',
            'tox>=2.7.0',
        ],
        'tox': [
            deps['djangorestframework'],
            deps['ldap3'],
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
