import os

from setuptools import setup, find_packages

__version__ = open("VERSION", 'r').read().strip()

REQUIREMENTS_FOLDER = os.getenv('REQUIREMENTS_PATH', '')

requirements = [line.strip() for line in open(os.path.join(REQUIREMENTS_FOLDER, "requirements.txt"), 'r')]

setup(
    name='ninjin',
    version=__version__,
    keywords="ninjin",
    packages=find_packages(exclude=['tests']),
    install_requires=requirements,
    extras_require={
        'dev': [
            'mock',
            'async-generator==1.10',
            'flake8',
            'flake8-eradicate',
            'flake8-print',
            'flake8-isort',
            'pytest',
            'pytest-factoryboy',
            'pytest-pep8',
            'pytest-mock==3.1.0',
            'pytest-asyncio==0.11.0',
        ]
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.5',
    ]
)
