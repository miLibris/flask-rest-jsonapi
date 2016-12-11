from setuptools import setup, find_packages


__version__ = '0.2'


setup(
    name="Flask-Rest-JSONAPI",
    version=__version__,
    description='Flask extension to create web api according to jsonapi specification with Flask, Marshmallow and data provider of your choice (SQLAlchemy, MongoDB, ...)',
    url='https://github.com/miLibris/flask-rest-jsonapi',
    author='miLibris',
    licence='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',
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
