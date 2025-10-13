"""
This is the file containing all of the endpoints for our flask app.
The endpoint called `endpoints` will return all available endpoints.
"""
# from http import HTTPStatus

from flask import Flask, request  # , request
from flask_restx import Resource, Api  # , fields  # Namespace
from flask_cors import CORS

# import werkzeug.exceptions as wz
import cities.queries as cqry

app = Flask(__name__)
CORS(app)
api = Api(app)

MESSAGE = 'Message'
ERROR = "Error"
READ = 'read'
POST = 'post'

ENDPOINT_EP = '/endpoints'
ENDPOINT_RESP = 'Available endpoints'

HELLO_EP = '/hello'
HELLO_RESP = 'hello'

CITIES_EPS = '/cities'
CITIES_RESP = 'Cities'


@api.route(f'{CITIES_EPS}')
class Cities(Resource):
    """
    The purpose of the HelloWorld class is to have a simple test to see if the
    app is working at all.
    """
    def get(self):
        """
        A trivial endpoint to see if the server is running.
        """
        try:
            cities = cqry.read()
        except ConnectionError as err:
            return {ERROR: str(err)}
        return {CITIES_RESP: cities}

    def post(self):
        """
        Create a new city
        """
        try:
            data = request.json
            city_id = cqry.create(data)
        except ConnectionError as err:
            return {ERROR: str(err)}
        except ValueError as err:
            return {ERROR: str(err)}
        return {CITIES_RESP: {"city_id": city_id}}


@api.route(HELLO_EP)
class HelloWorld(Resource):
    """
    The purpose of the HelloWorld class is to have a simple test to see if the
    app is working at all.
    """
    def get(self):
        """
        A trivial endpoint to see if the server is running.
        """
        return {HELLO_RESP: 'world'}


@api.route(ENDPOINT_EP)
class Endpoints(Resource):
    """
    This class will serve as live, fetchable documentation of what endpoints
    are available in the system.
    """
    def get(self):
        """
        The `get()` method will return a sorted list of available endpoints.
        """
        endpoints = sorted(rule.rule for rule in api.app.url_map.iter_rules())
        return {"Available endpoints": endpoints}
