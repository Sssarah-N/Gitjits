"""
Authentication endpoints - STEP BY STEP.
Starting with just register.
"""
from flask import request
from flask_restx import Resource, Namespace, fields

import users.queries as uqry

# Create namespace
auth_ns = Namespace('auth', description='Authentication operations')

# Model for register (for Swagger docs)
register_model = auth_ns.model('Register', {
    'username': fields.String(required=True, description='Username (3-20 chars)'),
    'email': fields.String(required=True, description='Email address'),
    'password': fields.String(required=True, description='Password (min 6 chars)')
})


@auth_ns.route('/register')
class Register(Resource):
    """User registration endpoint."""
    
    @auth_ns.expect(register_model)
    @auth_ns.doc(description='Register a new user')
    def post(self):
        """Register a new user account."""
        data = request.json
        if not data:
            return {'Error': 'Request body must contain JSON data'}, 400
        
        try:
            username = uqry.create_user(
                username=data.get('username'),
                email=data.get('email'),
                password=data.get('password')
            )
            
            return {
                'message': 'User registered successfully',
                'username': username
            }, 201
            
        except ValueError as e:
            return {'Error': str(e)}, 400
        except Exception as e:
            return {'Error': f'Registration failed: {str(e)}'}, 500


# We'll add login endpoint next!
