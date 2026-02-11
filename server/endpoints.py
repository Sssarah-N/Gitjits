"""
Flask API endpoints for geographic data management.
Handles CRUD operations for cities, states, and countries.
"""
from flask import Flask, request
from flask_restx import Resource, Api, Namespace
from flask_cors import CORS

import cities.queries as cqry
import states.queries as sqry
import countries.queries as coqry
import parks.queries as pqry
from server.models import register_models

# =============================================================================
# App Setup
# =============================================================================
app = Flask(__name__)
CORS(app)
api = Api(app, title='Geographic Data API', version='1.0',
          description='''API for managing cities, states, countries,
          and national parks.''')

# Register Swagger models
models = register_models(api)

# Namespaces
cities_ns = Namespace('cities', description='Cities operations')
states_ns = Namespace('states', description='States operations')
countries_ns = Namespace('countries', description='Countries operations')
parks_ns = Namespace('parks', description='National parks operations')

api.add_namespace(cities_ns, path='/cities')
api.add_namespace(states_ns, path='/states')
api.add_namespace(countries_ns, path='/countries')
api.add_namespace(parks_ns, path='/parks')

# Constants for tests and response keys
HELLO_EP = '/hello'
HELLO_RESP = 'hello'
ENDPOINT_EP = '/endpoints'
ENDPOINT_RESP = 'Available endpoints'
STATISTICS_EP = '/statistics'
STATISTICS_RESP = 'Statistics'

CITIES_EPS = '/cities'
CITIES_RESP = 'Cities'
CITY_RESP = 'City'

STATES_EPS = '/states'
STATES_RESP = 'States'
STATE_RESP = 'State'

COUNTRIES_EPS = '/countries'
COUNTRIES_RESP = 'Countries'
COUNTRY_RESP = 'Country'

PARKS_EPS = '/parks'
PARKS_RESP = 'Parks'
PARK_RESP = 'Park'

MESSAGE = 'Message'
ERROR = 'Error'


# =============================================================================
# Helper Functions
# =============================================================================
def handle_errors(func):
    """Decorator to handle common exceptions."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ConnectionError as err:
            return {'Error': str(err)}, 503
        except ValueError as err:
            return {'Error': str(err)}, 400
        except KeyError as err:
            return {'Error': str(err)}, 404
    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    return wrapper


# =============================================================================
# Cities Endpoints
# =============================================================================
@cities_ns.route('')
class Cities(Resource):
    """Operations on the cities collection."""

    @api.doc(description='Get all cities')
    @api.response(200, 'Success', models['cities_list'])
    @handle_errors
    def get(self):
        """Get all cities."""
        return {'Cities': cqry.read()}

    @api.expect(models['city'])
    @api.response(201, 'Created')
    @handle_errors
    def post(self):
        """Create a new city."""
        data = request.json
        if not data:
            return {'Error': 'Request body must contain JSON data'}, 400
        city_id = cqry.create(data)
        return {'Cities': {'_id': city_id}}, 201


@cities_ns.route('/<city_id>')
class City(Resource):
    """Operations on individual cities by MongoDB ObjectId."""

    @api.doc(params={'city_id': 'MongoDB ObjectId'})
    @api.response(200, 'Success', models['city'])
    @handle_errors
    def get(self, city_id):
        """Get a city by MongoDB ObjectId."""
        return {'City': cqry.get(city_id)}

    @api.expect(models['city'])
    @handle_errors
    def put(self, city_id):
        """Update a city by MongoDB ObjectId."""
        cqry.update(city_id, request.json)
        updated = cqry.get(city_id)
        return {'City': updated}

    @handle_errors
    def delete(self, city_id):
        """Delete a city by MongoDB ObjectId."""
        cqry.delete(city_id)
        return {'Message': f'City {city_id} deleted'}


@cities_ns.route('/by-state/<state_code>')
class CitiesByState(Resource):
    """Get cities filtered by state."""

    @api.doc(description='Get all cities in a state')
    @handle_errors
    def get(self, state_code):
        """Get all cities by state code (e.g., NY, CA)."""
        return {'Cities': cqry.get_by_state_code(state_code)}


# =============================================================================
# States Endpoints
# =============================================================================
@states_ns.route('')
class States(Resource):
    """Operations on the states collection."""

    @api.doc(description='Get all states')
    @api.response(200, 'Success', models['states_list'])
    @handle_errors
    def get(self):
        """Get all states."""
        return {'States': sqry.read()}

    @api.expect(models['state'])
    @api.response(201, 'Created')
    @handle_errors
    def post(self):
        """Create a new state."""
        data = request.json
        if not data:
            return {'Error': 'Request body must contain JSON data'}, 400
        state_code, country_code = sqry.create(data)
        return {'States': {
            'state_code': state_code,
            'country_code': country_code
        }}, 201


# =============================================================================
# Countries Endpoints
# =============================================================================
@countries_ns.route('')
class Countries(Resource):
    """Operations on the countries collection."""

    @api.doc(description='Get all countries')
    @api.response(200, 'Success', models['countries_list'])
    @handle_errors
    def get(self):
        """Get all countries."""
        return {'Countries': coqry.read()}

    @api.expect(models['country'])
    @api.response(201, 'Created')
    @handle_errors
    def post(self):
        """Create a new country."""
        data = request.json
        if not data:
            return {'Error': 'Request body must contain JSON data'}, 400
        code = coqry.create(data)
        return {'Countries': {'code': code}}, 201


@countries_ns.route('/<code>')
class Country(Resource):
    """Operations on individual countries by ISO code."""

    @api.doc(params={'code': 'ISO country code (e.g., US, CA, UK)'})
    @api.response(200, 'Success', models['country'])
    @handle_errors
    def get(self, code):
        """Get a country by ISO code."""
        return {'Country': coqry.get(code)}

    @api.expect(models['country'])
    @handle_errors
    def put(self, code):
        """Update a country by ISO code."""
        coqry.update(code, request.json)
        updated = coqry.get(code)
        return {'Country': updated}

    @handle_errors
    def delete(self, code):
        """Delete a country by ISO code."""
        coqry.delete(code)
        return {'Message': f'Country {code} deleted'}


@countries_ns.route('/<country_code>/states')
class StatesByCountry(Resource):
    """Get all states in a country."""

    @api.doc(params={'country_code': 'ISO country code (e.g., US, CA)'})
    @handle_errors
    def get(self, country_code):
        """Get all states in a country."""
        return {'States': sqry.get_states_by_country(country_code)}


@countries_ns.route('/<country_code>/states/<state_code>')
class StateByCode(Resource):
    """Operations on individual states by composite key."""

    @api.doc(params={
        'country_code': 'ISO country code (e.g., US)',
        'state_code': 'State/province code (e.g., NY)'
    })
    @handle_errors
    def get(self, country_code, state_code):
        """Get a state by country and state code."""
        return {'State': sqry.get(state_code, country_code)}

    @api.expect(models['state'])
    @handle_errors
    def put(self, country_code, state_code):
        """Update a state by country and state code."""
        sqry.update(state_code, country_code, request.json)
        updated = sqry.get(state_code, country_code)
        return {'State': updated}

    @handle_errors
    def delete(self, country_code, state_code):
        """Delete a state by country and state code."""
        sqry.delete(state_code, country_code)
        return {'Message': f'State {state_code} in {country_code} deleted'}


# =============================================================================
# Parks Endpoints
# =============================================================================
@parks_ns.route('')
class Parks(Resource):
    """Operations on the parks collection."""

    @api.doc(description='Get all parks')
    @api.response(200, 'Success', models['parks_list'])
    @handle_errors
    def get(self):
        """Get all parks."""
        # Note: You'll need to implement pqry.read() in parks/queries.py
        try:
            parks = pqry.read() if hasattr(pqry, 'read') else []
            return {'Parks': parks}
        except AttributeError:
            return {'Parks': []}

    @api.expect(models['park'])
    @api.response(201, 'Created')
    @handle_errors
    def post(self):
        """Create a new park."""
        data = request.json
        if not data:
            return {'Error': 'Request body must contain JSON data'}, 400
        park_id = pqry.create(data)
        return {'Parks': {'_id': park_id}}, 201


@parks_ns.route('/<park_id>')
class Park(Resource):
    """Operations on individual parks by MongoDB ObjectId."""

    @api.doc(params={'park_id': 'MongoDB ObjectId'})
    @api.response(200, 'Success', models['park'])
    @handle_errors
    def get(self, park_id):
        """Get a park by MongoDB ObjectId."""
        if hasattr(pqry, 'get'):
            return {'Park': pqry.get(park_id)}
        return {'Error': 'Park retrieval not implemented'}, 501

    @api.expect(models['park'])
    @handle_errors
    def put(self, park_id):
        """Update a park by MongoDB ObjectId."""
        if hasattr(pqry, 'update'):
            pqry.update(park_id, request.json)
            updated = pqry.get(park_id)
            return {'Park': updated}
        return {'Error': 'Park update not implemented'}, 501

    @handle_errors
    def delete(self, park_id):
        """Delete a park by MongoDB ObjectId."""
        if hasattr(pqry, 'delete'):
            pqry.delete(park_id)
            return {'Message': f'Park {park_id} deleted'}
        return {'Error': 'Park deletion not implemented'}, 501


# class ParksByState(Resource) for finding parks by state
@parks_ns.route('/state/<state_code>')
class ParksByState(Resource):
    """Operations to find parks by state code."""

    @api.doc(params={'state_code': 'Two-letter state code, e.g., CA'})
    @api.response(200, 'Success', models['parks_list'])
    @handle_errors
    def get(self, state_code):
        """Get all parks in a state."""
        try:
            parks = pqry.get_by_state(state_code)
            return {'Parks': parks}, 200
        except ValueError as e:
            return {'Error': str(e)}, 400
        except Exception:
            return {'Error': 'Internal server error'}, 500

# =============================================================================
# Utility Endpoints
# =============================================================================


@api.route('/hello')
class HelloWorld(Resource):
    """Health check endpoint."""

    def get(self):
        """Check if server is running."""
        return {'hello': 'world'}


@api.route('/statistics')
class Statistics(Resource):
    """Database statistics endpoint."""

    @handle_errors
    def get(self):
        """Get database statistics."""
        countries = coqry.read()
        states = sqry.read()
        cities = cqry.read()

        # Count states by country
        states_by_country = {}
        for state in states:
            code = state.get('country_code', 'Unknown')
            states_by_country[code] = states_by_country.get(code, 0) + 1

        # Count parks if available
        parks = []
        try:
            if hasattr(pqry, 'read'):
                parks = pqry.read()
        except Exception:
            pass

        return {
            'Statistics': {
                'total_countries': len(countries),
                'total_states': len(states),
                'total_cities': len(cities),
                'total_parks': len(parks),
                'states_by_country': states_by_country,
                'database': 'Gitjits',
                'collections': ['countries', 'states', 'cities', 'parks'],
            }
        }


@api.route('/endpoints')
class Endpoints(Resource):
    """List all available endpoints."""

    def get(self):
        """Get list of all API endpoints."""
        endpoints = sorted(
            rule.rule for rule in api.app.url_map.iter_rules()
        )
        return {'Available endpoints': endpoints}


@api.route('/delete-all-data')
class DeleteAllData(Resource):
    """Danger zone: Delete all data."""

    def delete(self):
        """Delete ALL data from the database. Use with caution!"""
        counts = {'cities': 0, 'states': 0, 'countries': 0}

        for city in cqry.read():
            try:
                cqry.delete(city.get('_id'))
                counts['cities'] += 1
            except Exception:
                pass

        for state in sqry.read():
            try:
                sqry.delete(
                    state.get('state_code'),
                    state.get('country_code')
                )
                counts['states'] += 1
            except Exception:
                pass

        for country in coqry.read():
            try:
                coqry.delete(country.get('code'))
                counts['countries'] += 1
            except Exception:
                pass

        total = counts['cities'] + counts['states'] + counts['countries']
        return {
            'Deleted': counts,
            'Message': f'Deleted {total} total items'
        }
