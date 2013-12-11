#!/usr/bin/env python
from setuptools import setup, find_packages


TEST_REQUIRES = [
    'flexmock>=0.9.7',
    'nose',
    'coverage'
]

INSTALL_REQUIRES = [
    'requests>=1.0.0',
    'pycrypto>=2.5',
    'python-dateutil>=1.5'
]

setup(
    name='uber.py',
    version='1.0.1',
    author='Tal Shiri',
    author_email='eiopaa@gmail.com',
    url='http://github.com/tals/uber.py',
    description='Python client for Uber',
    long_description=__doc__,
    packages=find_packages(exclude=("tests", "tests.*",)),
    zip_safe=False,
    extras_require={
        'tests': TEST_REQUIRES,
    },
    license='MIT',
    tests_require=TEST_REQUIRES,
    install_requires=INSTALL_REQUIRES,
    test_suite='tests',
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'ubercli = examples.ubercli:main',
        ]
    },
    classifiers=[
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Topic :: Software Development',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
    ],
)