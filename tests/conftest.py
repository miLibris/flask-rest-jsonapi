# -*- coding: utf-8 -*-

import pytest
from flask import Flask


@pytest.fixture(scope="session")
def app():
    app = Flask(__name__)
    yield app


@pytest.fixture
def app_non_scoped():
    app = Flask(__name__)
    yield app


@pytest.yield_fixture(scope="session")
def client(app):
    return app.test_client()
