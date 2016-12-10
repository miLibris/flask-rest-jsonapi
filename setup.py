from setuptools import setup, find_packages


__version__ = '0.1'


setup(
    name="flask-rest-jsonapi",
    version=__version__,
    author='miLibris',
    packages=find_packages(),
    description='flask-rest-jsonapi is a library that help you build rest api',
    setup_requires=['pytest-runner'],
    tests_require=['pytest']
)
