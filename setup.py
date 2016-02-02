import sys

from setuptools import find_packages, setup


PY_VERSION = sys.version_info[:2]
DJANGO_VERSION = '>=1.7,<1.9' if PY_VERSION >= (2, 7) else '>=1.6,<1.7'


with open('VERSION') as version_fp:
    VERSION = version_fp.read().strip()


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
    install_requires=[
        'stashward'
    ],
    extras_require={
        'ldap': [
            'ldap3',
        ],
        'test': [
            'django%s' % DJANGO_VERSION,
            'flake8',
            'ldap3',
            'mock',
            'model_mommy',
        ],
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Framework :: Django',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ],
)
