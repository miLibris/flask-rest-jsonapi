from setuptools import setup, find_packages


__version__ = '0.1'


setup(
    name="flask-rest-jsonapi",
    version=__version__,
    author='miLibris',
    packages=find_packages(),
    description='empty',
    setup_requires=['pytest-runner'],
    tests_require=['pytest'],
    test_suite="tests"
)
