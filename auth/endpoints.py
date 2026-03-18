
from flask import request
from flask_restx import Resource, Namespace, fields

import users.queries as uqry
from auth.jwt_utils import generate_token, token_required

# Create namespace
auth_ns = Namespace('auth', description='Authentication operations')

# Models for Swagger docs
register_model = auth_ns.model('Register', {
    'username': fields.String(required=True, description='Username (3-20 chars)'),
    'email': fields.String(required=True, description='Email address'),
    'password': fields.String(required=True, description='Password (min 6 chars)')
})

login_model = auth_ns.model('Login', {
    'username': fields.String(required=True, description='Username'),
    'password': fields.String(required=True, description='Password')
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


@auth_ns.route('/login')
class Login(Resource):
    """User login endpoint."""
    
    @auth_ns.expect(login_model)
    @auth_ns.doc(description='Login and receive JWT token')
    def post(self):
        """Authenticate user and return JWT token."""
        data = request.json
        if not data:
            return {'Error': 'Request body must contain JSON data'}, 400
        
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return {'Error': 'Username and password are required'}, 400
        
        try:
            # Authenticate user
            user = uqry.authenticate(username, password)
            
            # Generate JWT token
            token = generate_token(user['username'], user['role'])
            
            return {
                'token': token,
                'user': user,
                'message': 'Login successful'
            }, 200
            
        except ValueError as e:
            return {'Error': str(e)}, 401
        except Exception as e:
            return {'Error': 'Authentication failed'}, 401


@auth_ns.route('/me')
class CurrentUser(Resource):
    """Get current user information (protected endpoint)."""
    
    @auth_ns.doc(description='Get current user info (requires token)',
                 security='Bearer')
    @token_required
    def get(self, current_user):
        """Get information about the currently authenticated user."""
        try:
            user = uqry.get_user(current_user['username'])
            if user:
                # Remove sensitive info
                user.pop('password_hash', None)
                user.pop('_id', None)
                return {'user': user}, 200
            return {'Error': 'User not found'}, 404
        except Exception as e:
            return {'Error': str(e)}, 500
