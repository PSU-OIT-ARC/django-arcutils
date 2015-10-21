import sys

from setuptools import find_packages, setup


VERSION = '2.0.dev0'


install_requires = [
    'django-local-settings>=1.0a8',
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
        'cas': [
            'django-cas-client>=1.2.0',
        ],
        'ldap': [
            'ldap3>=0.9.9.1',
        ],
        'dev': [
            'django>=1.7',
            'flake8',
            'ldap3',
            'mock',
            'model_mommy',
        ],
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Framework :: Django',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ],
)
