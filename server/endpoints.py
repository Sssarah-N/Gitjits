"""
This is the file containing all of the endpoints for our flask app.
The endpoint called `endpoints` will return all available endpoints.
"""
# from http import HTTPStatus

from flask import Flask, request  # , request
from flask_restx import Resource, Api, fields  # Namespace
from flask_cors import CORS

# import werkzeug.exceptions as wz
import cities.queries as cqry

app = Flask(__name__)
CORS(app)
api = Api(app)

# Define the city model for Swagger documentation
city_model = api.model('City', {
    'name': fields.String(required=True, description='City name',
                          example='New York'),
    'state_code': fields.String(required=True, description='State code',
                                example='NY')
})

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
CITY_ID = 'city_id'
CITY_EP = '/cities/<city_id>'
CITY_RESP = 'City'


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

    @api.expect(city_model)
    def post(self):
        """
        Create a new city
        """
        try:
            data = request.json
            if data is None:
                return {ERROR: "Request body must contain JSON data"}, 400
            city_id = cqry.create(data)
        except ConnectionError as err:
            return {ERROR: str(err)}
        except ValueError as err:
            return {ERROR: str(err)}
        return {CITIES_RESP: {"city_id": city_id}}


@api.route(CITY_EP)
class City(Resource):
    """
    This class handles operations on individual cities.
    """
    def get(self, city_id):
        """
        Get a single city by ID.
        """
        try:
            city = cqry.get(city_id)
        except ValueError as err:
            return {ERROR: str(err)}, 400
        except KeyError as err:
            return {ERROR: str(err)}, 404
        return {CITY_RESP: city}

    @api.expect(city_model)
    def put(self, city_id):
        """
        Update a city by ID.
        """
        try:
            data = request.json
            updated_id = cqry.update(city_id, data)
        except ValueError as err:
            return {ERROR: str(err)}, 400
        except KeyError as err:
            return {ERROR: str(err)}, 404
        return {CITY_RESP: {CITY_ID: updated_id}}

    def delete(self, city_id):
        """
        Delete a city by ID.
        """
        try:
            cqry.delete(city_id)
        except ValueError as err:
            return {ERROR: str(err)}, 400
        except KeyError as err:
            return {ERROR: str(err)}, 404
        return {MESSAGE: f"City {city_id} deleted successfully"}


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
