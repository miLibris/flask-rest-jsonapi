from setuptools import setup, find_packages


__version__ = '0.3.1'


setup(
    name="Flask-Rest-JSONAPI",
    version=__version__,
    description='Flask extension to create web api according to jsonapi specification with Flask, Marshmallow and data \
                 provider of your choice (SQLAlchemy, MongoDB, ...)',
    url='https://github.com/miLibris/flask-rest-jsonapi',
    author='miLibris API Team',
    author_email='pf@milibris.net',
    license='MIT',
    classifiers=[
        'Framework :: Flask',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'License :: OSI Approved :: MIT License',
    ],
    keywords='web api jsonapi flask',
    packages=find_packages(exclude=['tests']),
    zip_safe=False,
    platforms='any',
    install_requires=['Flask',
                      'marshmallow_jsonapi',
                      'six',
                      'sqlalchemy',
                      'pymongo'],
    setup_requires=['pytest-runner'],
    tests_require=['pytest'],
    extras_require={'tests': 'pytest', 'docs': 'sphinx'}
)
