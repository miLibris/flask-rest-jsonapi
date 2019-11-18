from setuptools import setup, find_packages

__version__ = '0.30.4'

setup(
    name="flapison",
    version=__version__,
    description='Flask extension to create REST web api according to JSONAPI 1.0 specification with Flask, Marshmallow \
                 and data provider of your choice (SQLAlchemy, MongoDB, ...)',
    url='https://github.com/TMiguelT/flapison',
    author='Michael Milton',
    author_email='ttmigueltt@gmail.com',
    license='MIT',
    classifiers=[
        'Framework :: Flask',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'License :: OSI Approved :: MIT License',
    ],
    keywords='web api rest jsonapi flask sqlalchemy marshmallow',
    packages=find_packages(exclude=['tests']),
    zip_safe=False,
    platforms='any',
    install_requires=[
        'six',
        'Flask>=0.11',
        'marshmallow>=3.1.0',
        'marshmallow_jsonapi>=0.11.0',
        'sqlalchemy'
    ],
    setup_requires=['pytest-runner'],
    tests_require=['pytest'],
    extras_require={
        'dev': [
            'pytest',
            'coveralls',
            'coverage'
        ],
        'docs': 'sphinx'
    }
)
