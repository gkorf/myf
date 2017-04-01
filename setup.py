from setuptools import setup, find_packages
import os

PACKAGE_NAME = "myf"

CURPATH = os.path.dirname(os.path.realpath(__file__))
VERSION_FILE = os.path.join(CURPATH, "version.txt")
REQUIREMENTS_FILE = os.path.join(CURPATH, "requirements.txt")

with open(VERSION_FILE) as f:
    VERSION = f.read().strip()

with open(REQUIREMENTS_FILE) as f:
    INSTALL_REQUIRES = [
        x.strip('\n')
        for x in f.readlines()
        if x and x[0] != '#'
    ]


setup(
    name=PACKAGE_NAME,
    version=VERSION,
    license='GPL v3',
    author='Giorgos Korfiatis',
    author_email='korfiatis@gmail.com',
    description='Generate and upload Greek MYF tax entries',
    packages=find_packages(),
    install_requires=INSTALL_REQUIRES,
    entry_points={
        'console_scripts': {
            'myf=myf.myf:main'
        }
    }
)
