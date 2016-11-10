# -*- coding: utf-8 -*-

import pytest

from flask import Flask


@pytest.fixture(scope="session")
def app():
    app = Flask(__name__)
    return app


@pytest.yield_fixture(scope="session")
def client(app):
    with app.test_client() as client:
        yield client
