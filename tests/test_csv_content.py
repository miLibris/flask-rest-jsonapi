from csv import DictWriter, DictReader
from io import StringIO
from flask import make_response, Blueprint, Flask

import pytest

from flask_rest_jsonapi import Api

@pytest.fixture()
def app():
    app = Flask(__name__)
    return app


@pytest.yield_fixture()
def client(app):
    return app.test_client()

@pytest.fixture()
def csv_api(app, person_list, person_detail, person_computers, computer_list, computer_detail,
            computer_owner):
    bp = Blueprint('api', __name__)
    api = Api(blueprint=bp, response_renderers={
        'text/csv': render_csv
    }, request_parsers={
        'text/csv': parse_csv
    })
    api.route(person_list, 'person_list', '/persons')
    api.route(person_detail, 'person_detail', '/persons/<int:person_id>')
    api.route(person_computers, 'person_computers', '/persons/<int:person_id>/relationships/computers')
    api.route(person_computers, 'person_computers_owned', '/persons/<int:person_id>/relationships/computers-owned')
    api.route(person_computers, 'person_computers_error', '/persons/<int:person_id>/relationships/computer')
    api.route(computer_list, 'computer_list', '/computers', '/persons/<int:person_id>/computers')
    api.route(computer_list, 'computer_detail', '/computers/<int:id>')
    api.route(computer_owner, 'computer_owner', '/computers/<int:id>/relationships/owner')
    api.init_app(app)


def flatten_json(y):
    out = {}

    def flatten(x, name=''):
        if type(x) is dict:
            for a in x:
                flatten(x[a], name + a + '.')
        elif type(x) is list:
            i = 0
            for a in x:
                flatten(a, name + str(i) + '.')
                i += 1
        else:
            out[name[:-1]] = x

    flatten(y)
    return out


def render_csv(response):
    data = response['data']
    # Treat single values as a list of one element
    if not isinstance(data, list):
        data = [data]

    # Flatten the list of rows
    rows = []
    fields = set()
    for row in data:
        flattened = flatten_json(row)
        rows.append(flattened)
        fields.update(flattened.keys())

    # Write the rows to CSV
    with StringIO() as out:
        writer = DictWriter(out, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
        return make_response(out.getvalue(), 200, {
            'Content-Type': 'text/csv'
        })


def unflatten_json(obj):
    output = {}
    for key, value in obj.items():
        current_obj = output
        split = key.split('.')
        for i, segment in enumerate(split):
            # If the segment doesn't already exist, create it
            if segment not in current_obj:
                current_obj[segment] = {}

            if i == len(split) - 1:
                # If this is the last item, store it
                current_obj[segment] = value
            else:
                # If this is not the last item, go deeper into the tree
                current_obj = current_obj[segment]
    return output


def parse_csv(request):
    objects = []
    with StringIO(request.data.decode()) as fp:
        reader = DictReader(fp)
        for row in reader:
            objects.append(unflatten_json(row))

    # We only ever have to parse singleton rows
    objects = objects[0]

    return {'data': objects}


def test_csv_response(csv_api, person, person_2, client):
    response = client.get('/persons', headers={
        'Content-Type': 'application/vnd.api+json',
        'Accept': 'text/csv'
    })
    rows = list(DictReader(response.data.decode().split()))

    # Since we used person and person2, there should be 2 rows
    assert len(rows) == 2

    # The names should be in the dictionary
    names = set([row['attributes.name'] for row in rows])
    assert 'test' in names
    assert 'test2' in names


def test_csv_request(csv_api, client, person_schema):
    with StringIO() as fp:
        writer = DictWriter(fp, fieldnames=['attributes.name', 'type'])
        writer.writeheader()
        writer.writerow({
            'attributes.name': 'one',
            'type': 'person'
        })

        response = client.post('/persons', data=fp.getvalue(), headers={
            'Content-Type': 'text/csv',
            'Accept': 'application/vnd.api+json'
        })

    # A new row was created
    assert response.status_code == 201

    # The returned data had the same name we posted
    assert response.json['data']['attributes']['name'] == 'one'
