# Based on https://github.com/pypa/sampleproject

# Always prefer setuptools over distutils
from setuptools import setup, find_packages
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='mlox',
    version='1.0',
    description='A tool for analyzing and sorting your Morrowind plugin load order.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/mlox/mlox',
    author='Arthur Moore',
    author_email='AMoore-pip@cd-net.net',
    classifiers=[
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Topic :: Games/Entertainment',
    ],
    keywords='Morrowind Modding',
    packages=['mlox', 'mlox.static'],
    package_data={
        'mlox.static': [
            'window.qml',
            'mlox.gif',
            'mlox.ico',
            'mlox.msg',
    ]},
    include_package_data=True,
    python_requires='>=3.5',
    install_requires=['colorama', 'appdirs', 'pyqt5', 'py7zr'],
    entry_points={
        'console_scripts': [
            'mlox=mlox.__main__:main',
        ],
    },
)
