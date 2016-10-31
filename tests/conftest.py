# -*- coding: utf-8 -*-

import pytest

from flask import Flask


@pytest.fixture
def app():
    app = Flask(__name__)

    @app.route("/", endpoint='test')
    def test():
        pass

    return app
