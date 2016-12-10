from setuptools import setup, find_packages


__version__ = '0.1'


setup(
    name="flask-rest-jsonapi",
    version=__version__,
    description='flask-rest-jsonapi is a library that help you build rest api',
    url='https://github.com/miLibris/flask-rest-jsonapi',
    author='miLibris',
    licence='MIT',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    keywords='web api jsonapi flask',
    packages=find_packages(),
    install_requires=['Flask',
                      'marshmallow_jsonapi',
                      'sqlalchemy',
                      'pymongo',
                      'pytest',
                      'sphinx'],
    setup_requires=['pytest-runner'],
    tests_require=['pytest']
)
