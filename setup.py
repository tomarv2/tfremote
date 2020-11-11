import os
from setuptools import find_packages, setup

VERSION = "0.0.2"

ROOT_PATH = os.path.abspath(os.path.dirname(__file__))


def get_requirements(env):
    try:
        with open("requirements-{}.txt".format(env)) as fp:
            return [x.strip() for x in fp.read().split("\n") if not x.startswith("#")]
    except:
        with open("requirements.txt".format(env)) as fp:
            return [x.strip() for x in fp.read().split("\n") if not x.startswith("#")]


install_requires = get_requirements("base")

with open("README.md") as f:
    long_description = f.read()

setup(
    name='tfremote',
    version=VERSION,
    license='MIT',
    description='Terraform wrapper to manage state across multiple cloud providers',
    long_description=long_description,
    long_description_content_type="text/markdown",
    author='Varun Tomar',
    author_email='varuntomar2019@gmail.com',
    python_requires=">=3.6",
    packages=find_packages(),
    install_requires=install_requires,
    url="https://github.com/tomarv2/tfremote",
    classifiers=[
        'Programming Language :: Python :: 3.6',
        'Operating System :: OS Independent',
    ],
    entry_points='''
        [console_scripts]
        tf = src.cli:entrypoint
    '''
)
