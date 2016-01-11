import sys

from setuptools import find_packages, setup


with open('VERSION') as version_fp:
    VERSION = version_fp.read().strip()


install_requires = [
    'django-local-settings>=1.0a13',
    'stashward',
]

if sys.version_info[:2] < (3, 4):
    install_requires.append('enum34')


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
            'certifi>=2015.11.20.1',
            'ldap3>=1.0.3',
        ],
        'dev': [
            'django>=1.7,<1.9',
            'djangorestframework>3.3',
            'flake8',
            'ldap3',
        ],
    },
    entry_points="""
    [console_scripts]
    arcutils = arcutils.__main__:main

    """,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Framework :: Django',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ],
)
