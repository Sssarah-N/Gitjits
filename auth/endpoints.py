
from flask import request
from flask_restx import Resource, Namespace, fields

import users.queries as uqry
from auth.jwt_utils import generate_token, token_required, admin_required
import examples.form_filler as ff

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


@auth_ns.route('/register-form')
class RegisterForm(Resource):
    """Get register form definition (HATEOAS)."""
    
    @auth_ns.doc(description='Get registration form with dynamic fields')
    def get(self):
        """
        Returns form definition for registration.
        Frontend uses this to build the form dynamically.
        """
        form_definition = [
            {
                ff.FLD_NM: 'username',
                ff.QSTN: 'Username:',
                ff.PARAM_TYPE: ff.QUERY_STR,
                ff.OPT: False,
                ff.DESCR: 'Choose a unique username (3-20 characters)'
            },
            {
                ff.FLD_NM: 'email',
                ff.QSTN: 'Email:',
                ff.PARAM_TYPE: ff.QUERY_STR,
                ff.OPT: False,
                ff.DESCR: 'Your email address'
            },
            {
                ff.FLD_NM: 'password',
                ff.QSTN: 'Password:',
                ff.PARAM_TYPE: ff.QUERY_STR,
                ff.INPUT_TYPE: ff.PASSWORD,
                ff.OPT: False,
                ff.DESCR: 'Password (minimum 6 characters)'
            }
        ]
        
        return {
            'form': form_definition,
            'submit_url': '/auth/register',
            'method': 'POST'
        }, 200


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
                password=data.get('password'),
                role='user'  # Force all new registrations to be regular users
            )
            
            return {
                'message': 'User registered successfully',
                'username': username
            }, 201
            
        except ValueError as e:
            return {'Error': str(e)}, 400
        except Exception as e:
            return {'Error': f'Registration failed: {str(e)}'}, 500


@auth_ns.route('/login-form')
class LoginForm(Resource):
    """Get login form definition (HATEOAS)."""
    
    @auth_ns.doc(description='Get login form structure')
    def get(self):
        """
        Returns form definition for login.
        Frontend uses this to build the login form dynamically.
        """
        form_definition = [
            {
                ff.FLD_NM: 'username',
                ff.QSTN: 'Username:',
                ff.PARAM_TYPE: ff.QUERY_STR,
                ff.OPT: False,
            },
            {
                ff.FLD_NM: 'password',
                ff.QSTN: 'Password:',
                ff.PARAM_TYPE: ff.QUERY_STR,
                ff.INPUT_TYPE: ff.PASSWORD,
                ff.OPT: False,
            }
        ]
        
        return {
            'form': form_definition,
            'submit_url': '/auth/login',
            'method': 'POST'
        }, 200


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


@auth_ns.route('/me/saved-parks')
class SavedParks(Resource):
    """Manage user's saved parks list."""
    
    @auth_ns.doc(description='Get saved parks (requires token)',
                 security='Bearer')
    @token_required
    def get(self, current_user):
        """Get list of parks saved by current user."""
        try:
            saved_parks = uqry.get_saved_parks(current_user['username'])
            return {'saved_parks': saved_parks}, 200
        except Exception as e:
            return {'Error': str(e)}, 500
    
    @auth_ns.doc(description='Add park to saved list (requires token)',
                 security='Bearer')
    @token_required
    def post(self, current_user):
        """Add a park to saved list."""
        data = request.json
        if not data or 'park_code' not in data:
            return {'Error': 'park_code is required'}, 400
        
        try:
            park_code = data['park_code']
            added = uqry.add_saved_park(current_user['username'], park_code)
            
            if added:
                return {'message': f'Park {park_code} added to saved'}, 201
            else:
                return {'message': f'Park {park_code} already saved'}, 200
        except ValueError as e:
            return {'Error': str(e)}, 400
        except Exception as e:
            return {'Error': str(e)}, 500


@auth_ns.route('/me/saved-parks/<park_code>')
class SavedPark(Resource):
    """Remove specific park from saved list."""
    
    @auth_ns.doc(params={'park_code': 'Park code to remove'},
                 description='Remove park from saved list (requires token)',
                 security='Bearer')
    @token_required
    def delete(self, park_code, current_user):
        """Remove a park from saved list."""
        try:
            removed = uqry.remove_saved_park(current_user['username'], park_code)
            
            if removed:
                return {'message': f'Park {park_code} removed from saved'}, 200
            else:
                return {'Error': f'Park {park_code} not in saved list'}, 404
        except ValueError as e:
            return {'Error': str(e)}, 400
        except Exception as e:
            return {'Error': str(e)}, 500


# Admin model for creating admin users
admin_create_model = auth_ns.model('CreateAdmin', {
    'username': fields.String(required=True, description='Username'),
    'email': fields.String(required=True, description='Email address'),
    'password': fields.String(required=True, description='Password')
})


@auth_ns.route('/admin/create')
class CreateAdminUser(Resource):
    """Admin-only endpoint to create new admin users."""
    
    @auth_ns.expect(admin_create_model)
    @auth_ns.doc(description='Create admin user (admin only)',
                 security='Bearer')
    @admin_required
    def post(self, current_user):
        """Create a new admin user. Only accessible to existing admins."""
        data = request.json
        if not data:
            return {'Error': 'Request body must contain JSON data'}, 400
        
        try:
            username = uqry.create_user(
                username=data.get('username'),
                email=data.get('email'),
                password=data.get('password'),
                role='admin'  # Force admin role
            )
            
            return {
                'message': 'Admin user created successfully',
                'username': username,
                'created_by': current_user['username']
            }, 201
            
        except ValueError as e:
            return {'Error': str(e)}, 400
        except Exception as e:
            return {'Error': f'Admin creation failed: {str(e)}'}, 500
