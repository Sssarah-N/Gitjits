"""
HATEOAS: Options endpoint for login/register forms.
"""
from flask_restx import Resource, Namespace

# Create namespace for options
options_ns = Namespace('options', description='Dropdown options for forms')


@options_ns.route('/roles')
class RoleOptions(Resource):
    """Get available user roles for dropdown."""
    
    @options_ns.doc(description='Get user role options for dropdowns')
    def get(self):
        """
        Returns list of available user roles.
        Use this for role dropdown in user registration.
        """
        options = [
            {'value': 'user', 'label': 'Regular User'},
            {'value': 'admin', 'label': 'Administrator'}
        ]
        return {'options': options}, 200
