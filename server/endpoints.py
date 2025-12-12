"""
This is the file containing all of the endpoints for our flask app.
The endpoint called `endpoints` will return all available endpoints.
"""
# from http import HTTPStatus

from flask import Flask, request  # , request
from flask_restx import Resource, Api, fields, Namespace  # Namespace
from flask_cors import CORS

# import werkzeug.exceptions as wz
import cities.queries as cqry
import states.queries as sqry
import countries.queries as coqry

app = Flask(__name__)
CORS(app)
api = Api(app)

# Swagger docs namespaces
cities_ns = Namespace('cities', description='Cities operations')
states_ns = Namespace('states', description='States operations')
countries_ns = Namespace('countries', description='Countries operations')

api.add_namespace(cities_ns, path='/cities')
api.add_namespace(states_ns, path='/states')
api.add_namespace(countries_ns, path='/countries')

# Define the city model for Swagger documentation
city_model = api.model('City', {
    'name': fields.String(required=True, description='City name',
                          example='New York'),
    'state_code': fields.String(required=True, description='State code',
                                example='NY')
})

# Define the state model for Swagger documentation
state_model = api.model('State', {
    'name': fields.String(required=True, description='State name',
                          example='New York'),
    'state_code': fields.String(required=True,
                                description='State code (composite key)',
                                example='NY'),
    'country_code': fields.String(required=True,
                                  description='Country code (composite key)',
                                  example='US'),
    'capital': fields.String(required=False, description='Capital city',
                             example='Albany'),
    'population': fields.Integer(required=False,
                                 description='State population',
                                 example=19450000)
})

# Define the country model for Swagger documentation
country_model = api.model('Country', {
    'name': fields.String(required=True, description='Country name',
                          example='United States'),
    'code': fields.String(required=False,
                          description='ISO country code',
                          example='US'),
    'capital': fields.String(required=False, description='Capital city',
                             example='Washington, D.C.'),
    'population': fields.Integer(required=False,
                                 description='Country population',
                                 example=331000000),
    'continent': fields.String(required=False, description='Continent',
                               example='North America')
})

# Define error message model for Swagger documentation
error_model = api.model('Error', {
    'message': fields.String(required=True, description='Error message',
                             example='Error message here')
})

# Define message model for Swagger documentation
message_model = api.model('Message', {
    'message': fields.String(required=True, description='Message',
                             example='Message here')
})

# Define cities model for Swagger documentation
cities_model = api.model('Cities', {
    'Cities': fields.List(
        fields.Nested(city_model),
        required=True,
        description='List of cities',
        example=[{'city_id': '693b8bd5159f4d68e5f79447'}],
    )
})

# Define states model for Swagger documentation
states_model = api.model('States', {
    'States': fields.List(
        fields.Nested(state_model),
        required=True,
        description='List of states with their IDs',
        example=[{'state_id': '693b8bd5159f4d68e5f79447'}],
    )
})

CITY_ID_DOC = 'ID of the city (MongoDB ObjectId)'
STATE_ID_DOC = 'ID of the state (MongoDB ObjectId)'

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

STATES_EPS = '/states'
STATES_RESP = 'States'
STATE_ID = 'state_id'
STATE_EP = '/states/<state_id>'
STATE_RESP = 'State'

COUNTRIES_EPS = '/countries'
COUNTRIES_RESP = 'Countries'
COUNTRY_ID = 'country_id'
COUNTRY_EP = '/countries/<country_id>'
COUNTRY_RESP = 'Country'

CITIES_BY_STATE_EP = '/cities/by-state/<state_code>'

STATISTICS_EP = '/statistics'
STATISTICS_RESP = 'Statistics'

DELETE_ALL_EP = '/delete-all-data'
DELETE_ALL_RESP = 'Deleted'


@cities_ns.route('')
class Cities(Resource):
    """
    The purpose of the HelloWorld class is to have a simple test to see if the
    app is working at all.
    """
    @api.doc(description='Get all cities')
    @api.response(200, 'Success', cities_model)
    @api.response(400, 'Bad Request', error_model)
    @api.response(503, 'Database connection error', error_model)
    def get(self):
        """
        A trivial endpoint to see if the server is running.
        """
        try:
            cities = cqry.read()
        except ConnectionError as err:
            return {ERROR: str(err)}, 503
        return {CITIES_RESP: cities}

    @api.expect(city_model)
    @api.response(200, 'Success', cities_model)
    @api.response(400, 'Bad Request', error_model)
    @api.response(503, 'Database connection error', error_model)
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
            return {ERROR: str(err)}, 503
        except ValueError as err:
            return {ERROR: str(err)}, 400
        return {CITIES_RESP: {"city_id": city_id}}


@cities_ns.route('/<city_id>')
class City(Resource):
    """
    This class handles operations on individual cities.
    """
    @api.doc(params={'city_id': CITY_ID_DOC})
    @api.response(200, 'Success', city_model)
    @api.response(400, 'Bad Request', error_model)
    @api.response(404, 'Not Found', error_model)
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
    @api.doc(params={
        'city_id': CITY_ID_DOC,
        'payload': 'Updated city fields'
    })
    @api.response(200, 'Success', city_model)
    @api.response(400, 'Bad Request', error_model)
    @api.response(404, 'Not Found', error_model)
    def put(self, city_id):
        """
        Update a city by ID.
        """
        try:
            data = request.json
            cqry.update(city_id, data)
            updated_city = cqry.get(city_id)
            updated_city['city_id'] = updated_city.get('id', city_id)
        except ValueError as err:
            return {ERROR: str(err)}, 400
        except KeyError as err:
            return {ERROR: str(err)}, 404
        return {CITY_RESP: updated_city}, 200

    @api.doc(params={'city_id': CITY_ID_DOC})
    @api.response(200, 'Success', message_model)
    @api.response(400, 'Bad Request', error_model)
    @api.response(404, 'Not Found', error_model)
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


@states_ns.route('')
class States(Resource):
    """
    This class handles operations on the states collection.
    """
    @api.doc(description='Get all states')
    @api.response(200, 'Success', states_model)
    @api.response(400, 'Bad Request', error_model)
    @api.response(503, 'Database connection error', error_model)
    def get(self):
        """
        Get all states.
        """
        try:
            states = sqry.read()
        except ConnectionError as err:
            return {ERROR: str(err)}, 503
        return {STATES_RESP: states}

    @api.expect(state_model)
    @api.response(200, 'Success', states_model)
    @api.response(400, 'Bad Request', error_model)
    @api.response(503, 'Database connection error', error_model)
    def post(self):
        """
        Create a new state
        """
        try:
            data = request.json
            if data is None:
                return {ERROR: "Request body must contain JSON data"}, 400
            state_id = sqry.create(data)
        except ConnectionError as err:
            return {ERROR: str(err)}, 503
        except ValueError as err:
            return {ERROR: str(err)}, 400
        return {STATES_RESP: {"state_id": state_id}}


@states_ns.route('/<state_id>')
class State(Resource):
    """
    This class handles operations on individual states.
    """
    @api.doc(params={'state_id': STATE_ID_DOC})
    @api.response(200, 'Success', state_model)
    @api.response(400, 'Bad Request', error_model)
    @api.response(404, 'Not Found', error_model)
    def get(self, state_id):
        """
        Get a single state by ID.
        """
        try:
            state = sqry.get(state_id)
        except ValueError as err:
            return {ERROR: str(err)}, 400
        except KeyError as err:
            return {ERROR: str(err)}, 404
        return {STATE_RESP: state}

    @api.expect(state_model)
    @api.doc(params={
        'state_id': STATE_ID_DOC,
        'payload': 'Updated state fields'
    })
    @api.response(200, 'Success', state_model)
    @api.response(400, 'Bad Request', error_model)
    @api.response(404, 'Not Found', error_model)
    def put(self, state_id):
        """
        Update a state by ID.
        """
        try:
            data = request.json
            sqry.update(state_id, data)
            updated_state = sqry.get(state_id)
            updated_state['state_id'] = updated_state.get('id', state_id)
        except ValueError as err:
            return {ERROR: str(err)}, 400
        except KeyError as err:
            return {ERROR: str(err)}, 404
        return {STATE_RESP: updated_state}, 200

    @api.doc(params={'state_id': STATE_ID_DOC})
    @api.response(200, 'Success', message_model)
    @api.response(400, 'Bad Request', error_model)
    @api.response(404, 'Not Found', error_model)
    def delete(self, state_id):
        """
        Delete a state by ID.
        """
        try:
            sqry.delete(state_id)
        except ValueError as err:
            return {ERROR: str(err)}, 400
        except KeyError as err:
            return {ERROR: str(err)}, 404
        return {MESSAGE: f"State {state_id} deleted successfully"}


@cities_ns.route('/by-state/<state_code>')
class CitiesByState(Resource):
    """
    Get all cities by state code.
    """
    @api.doc(description='Get all cities by state code')
    @api.response(200, 'Success', cities_model)
    @api.response(400, 'Bad Request', error_model)
    @api.response(503, 'Database connection error', error_model)
    def get(self, state_code):
        """
        Get all cities in a given state by state code.
        Example: /cities/by-state/NY returns all cities in New York
        """
        try:
            filtered = cqry.get_by_state_code(state_code)
            return {CITIES_RESP: filtered}
        except ConnectionError as err:
            return {ERROR: str(err)}, 503


@api.route(STATISTICS_EP)
class Statistics(Resource):
    """
    Get comprehensive database statistics.
    Provides counts and metadata for all geographic entities.
    """
    def get(self):
        """
        Get overall database statistics.
        Returns total counts for countries, states, and cities,
        plus metadata about the database.
        """
        try:
            # Get counts
            countries = coqry.read()
            states = sqry.read()
            cities = cqry.read()

            # Calculate statistics
            stats = {
                'total_countries': len(countries),
                'total_states': len(states),
                'total_cities': len(cities),
                'database': 'Gitjits',
                'collections': ['countries', 'states', 'cities'],
            }

            # Optional: Add breakdown by country if data available
            country_breakdown = {}
            for state in states:
                country_code = state.get('country_code', 'Unknown')
                country_breakdown[country_code] = country_breakdown.get(
                    country_code, 0) + 1

            if country_breakdown:
                stats['states_by_country'] = country_breakdown

            return {STATISTICS_RESP: stats}
        except ConnectionError as err:
            return {ERROR: str(err)}, 503
        except Exception as err:
            return {ERROR: f'Error getting statistics: {str(err)}'}, 500


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


@countries_ns.route('')
class Countries(Resource):
    """
    This class handles operations on the countries collection.
    """
    def get(self):
        """
        Get all countries.
        Returns a list of all countries in the database.
        """
        try:
            countries = coqry.read()
        except ConnectionError as err:
            return {ERROR: str(err)}, 503
        return {COUNTRIES_RESP: countries}

    @api.expect(country_model)
    @api.response(200, 'Country created successfully')
    @api.response(400, 'Validation error')
    @api.response(503, 'Database connection error')
    def post(self):
        """
        Create a new country.
        Requires 'name' field. Optional: code, capital, population,
        continent.
        """
        try:
            data = request.json
            if data is None:
                return {ERROR: "Request body must contain JSON data"}, 400
            country_id = coqry.create(data)
        except ConnectionError as err:
            return {ERROR: str(err)}, 503
        except ValueError as err:
            return {ERROR: str(err)}, 400
        return {COUNTRIES_RESP: {"country_id": country_id}}


@countries_ns.route('/<country_id>')
class Country(Resource):
    """
    This class handles operations on individual countries.
    """
    @api.response(200, 'Success')
    @api.response(400, 'Invalid ID')
    @api.response(404, 'Country not found')
    def get(self, country_id):
        """
        Get a single country by ID.
        Returns detailed information about a specific country.
        """
        try:
            country = coqry.get(country_id)
        except ValueError as err:
            return {ERROR: str(err)}, 400
        except KeyError as err:
            return {ERROR: str(err)}, 404
        return {COUNTRY_RESP: country}

    @api.expect(country_model)
    @api.response(200, 'Country updated successfully')
    @api.response(400, 'Validation error')
    @api.response(404, 'Country not found')
    def put(self, country_id):
        """
        Update a country by ID.
        All fields are optional. Only provided fields will be updated.
        """
        try:
            data = request.json
            coqry.update(country_id, data)
            updated_country = coqry.get(country_id)
            updated_country['country_id'] = updated_country.get(
                'id', country_id)
        except ValueError as err:
            return {ERROR: str(err)}, 400
        except KeyError as err:
            return {ERROR: str(err)}, 404
        return {COUNTRY_RESP: updated_country}, 200

    @api.response(200, 'Country deleted successfully')
    @api.response(400, 'Invalid ID')
    @api.response(404, 'Country not found')
    def delete(self, country_id):
        """
        Delete a country by ID.
        This will permanently remove the country from the database.
        """
        try:
            coqry.delete(country_id)
        except ValueError as err:
            return {ERROR: str(err)}, 400
        except KeyError as err:
            return {ERROR: str(err)}, 404
        return {MESSAGE: f"Country {country_id} deleted successfully"}


@api.route(DELETE_ALL_EP)
class DeleteAllData(Resource):
    """
    Delete all test data from the database.
    WARNING: This will delete ALL countries, states, and cities!
    Use for testing and development only.
    """
    def delete(self):
        """
        Delete all data from all collections.
        Returns count of deleted items.

        **WARNING**: This operation cannot be undone!
        Use only in testing/development environments.
        """
        try:
            deleted_counts = {}

            # Delete all cities
            cities = cqry.read()
            city_count = 0
            for city in cities:
                try:
                    cqry.delete(city.get('id'))
                    city_count += 1
                except Exception:
                    pass
            deleted_counts['cities'] = city_count

            # Delete all states
            states = sqry.read()
            state_count = 0
            for state in states:
                try:
                    sqry.delete(state.get('id'))
                    state_count += 1
                except Exception:
                    pass
            deleted_counts['states'] = state_count

            # Delete all countries
            countries = coqry.read()
            country_count = 0
            for country in countries:
                try:
                    coqry.delete(country.get('id'))
                    country_count += 1
                except Exception:
                    pass
            deleted_counts['countries'] = country_count

            return {
                DELETE_ALL_RESP: deleted_counts,
                MESSAGE: f"Deleted {city_count} cities, {state_count} "
                         f"states, {country_count} countries"
            }
        except Exception as err:
            return {ERROR: f'Error deleting data: {str(err)}'}, 500


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
