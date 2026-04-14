"""
Developer endpoints - admin only.
For debugging and monitoring, not for end users.
"""
import os
from flask_restx import Resource, Namespace
from auth.jwt_utils import admin_required

# Create namespace
dev_ns = Namespace('dev', description='Developer tools (admin only)')


@dev_ns.route('/logs')
class Logs(Resource):
    """View server logs (admin only)."""
    @dev_ns.doc(description='View application logs (admin only)',
                security='Bearer')
    @admin_required
    def get(self, current_user):
        """
        Get recent application logs from PythonAnywhere.
        Only accessible to admin users.
        Reads from /var/log/ directory.
        """
        try:
            # Get username from environment or config
            pa_username = os.environ.get('PA_USERNAME', 'YOUR_USERNAME')
            # PythonAnywhere log paths
            base = '/var/log'
            error_log = f'{base}/{pa_username}.pythonanywhere.com.error.log'
            server_log = f'{base}/{pa_username}.pythonanywhere.com.server.log'
            logs = {}
            # Try to read error log
            if os.path.exists(error_log):
                with open(error_log, 'r') as f:
                    lines = f.readlines()
                    logs['error_log'] = {
                        'lines': lines[-50:],
                        'total_lines': len(lines)
                    }

            # Try to read server log
            if os.path.exists(server_log):
                with open(server_log, 'r') as f:
                    lines = f.readlines()
                    logs['server_log'] = {
                        'lines': lines[-50:],
                        'total_lines': len(lines)
                    }

            # If no logs found
            if not logs:
                return {
                    'message': 'No log files found',
                    'note': 'Set PA_USERNAME environment variable',
                    'accessed_by': current_user['username']
                }, 200

            return {
                'logs': logs,
                'accessed_by': current_user['username'],
                'showing': 'Last 50 lines of each log'
            }, 200

        except Exception as e:
            return {'Error': str(e)}, 500
