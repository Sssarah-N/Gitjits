"""
Swagger documentation models for the API.
Separated from endpoints.py for better code organization.
"""
from flask_restx import fields


def register_models(api):
    """
    Register all Swagger models with the API instance.

    Args:
        api: Flask-RESTX Api instance

    Returns:
        dict: Dictionary containing all registered models
    """

    # Entity models
    city_model = api.model('City', {
        'name': fields.String(
            required=True, description='City name', example='New York'),
        'state_code': fields.String(
            required=True, description='State code', example='NY')
    })

    state_model = api.model('State', {
        'name': fields.String(
            required=True, description='State name', example='New York'),
        'state_code': fields.String(
            required=True, description='State code', example='NY'),
        'country_code': fields.String(
            required=True, description='Country code', example='US'),
        'capital': fields.String(
            description='Capital city', example='Albany'),
        'population': fields.Integer(
            description='Population', example=19450000)
    })

    country_model = api.model('Country', {
        'name': fields.String(
            required=True, description='Country name', example='USA'),
        'code': fields.String(
            description='ISO country code', example='US'),
        'capital': fields.String(
            description='Capital city', example='Washington, D.C.'),
        'population': fields.Integer(
            description='Population', example=331000000),
        'continent': fields.String(
            description='Continent', example='North America')
    })

    park_model = api.model('Park', {
        'name': fields.String(
            required=True, description='Park name',
            example='Abraham Lincoln Birthplace National Historical Park'),
        'state_code': fields.String(
            required=True, description='State code', example='KY')
    })

    # Response models
    error_model = api.model('Error', {
        'Error': fields.String(required=True, description='Error message')
    })

    message_model = api.model('Message', {
        'Message': fields.String(required=True, description='Success message')
    })

    # List response models
    cities_list = api.model('CitiesList', {
        'Cities': fields.List(
            fields.Nested(city_model), description='List of cities')
    })

    states_list = api.model('StatesList', {
        'States': fields.List(
            fields.Nested(state_model), description='List of states')
    })

    countries_list = api.model('CountriesList', {
        'Countries': fields.List(
            fields.Nested(country_model), description='List of countries')
    })

    parks_list = api.model('ParksList', {
        'Parks': fields.List(
            fields.Nested(park_model), description='List of parks')
    })

    return {
        'city': city_model,
        'state': state_model,
        'country': country_model,
        'park': park_model,
        'error': error_model,
        'message': message_model,
        'cities_list': cities_list,
        'states_list': states_list,
        'countries_list': countries_list,
        'parks_list': parks_list,
    }
