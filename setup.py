from setuptools import setup, find_packages


__version__ = '0.1'


setup(
    name="jsonapi-utils",
    version=__version__,
    author='python-jsonapi',
    packages=find_packages(),
    description='empty',
    setup_requires=['pytest-runner'],
    tests_require=['pytest']
)
