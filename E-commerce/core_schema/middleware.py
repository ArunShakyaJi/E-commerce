"""
Middleware for automatic token refresh
"""

from rest_framework_simplejwt.tokens import UntypedToken, RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.utils.deprecation import MiddlewareMixin
from supabase import create_client, Client
from decouple import config
import json

# Initialize Supabase client
SUPABASE_URL = str(config('Database_Url'))
SUPABASE_KEY = str(config('Database_key'))

# Ensure environment variables are loaded
if not SUPABASE_URL or not SUPABASE_KEY or SUPABASE_URL == 'None' or SUPABASE_KEY == 'None':
    raise ValueError("Missing Supabase configuration. Please check your .env file.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

class AutoTokenRefreshMiddleware(MiddlewareMixin):
    """
    Middleware to automatically refresh expired access tokens
    """
    def process_request(self, request):
        # Skip for non-API requests or requests that don't need authentication
        if not request.path.startswith('/api/') or request.path in ['/api/login/', '/api/signup/', '/api/refresh/']:
            return None
            
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if not auth_header or not auth_header.startswith('Bearer '):
            return None
            
        access_token = auth_header.split(' ')[1]
        
        try:
            # Try to validate the current access token
            UntypedToken(access_token)
            # Token is valid, continue
            return None
        except TokenError:
            # Token is invalid/expired, try to refresh it
            refresh_token = self.get_refresh_token_from_request(request)
            if refresh_token:
                try:
                    # Try to refresh the token
                    refresh = RefreshToken(refresh_token)
                    new_access_token = refresh.access_token
                    
                    # Add custom claims to new access token
                    user_id = refresh.get('user_id')
                    if user_id:
                        # Get updated user data from Supabase
                        user_result = supabase.table('auth_user').select('*').eq('id', user_id).execute()
                        if user_result.data:
                            user = user_result.data[0]
                            new_access_token['user_id'] = user.get('id')
                            new_access_token['username'] = user.get('username')
                            new_access_token['email'] = user.get('email')
                            new_access_token['is_staff'] = user.get('is_staff', False)
                            new_access_token['is_superuser'] = user.get('is_superuser', False)
                            new_access_token['is_active'] = user.get('is_active', True)
                    
                    # Update the authorization header with new token
                    request.META['HTTP_AUTHORIZATION'] = f'Bearer {str(new_access_token)}'
                    
                    # Set a flag to indicate token was refreshed
                    request.token_refreshed = True
                    request.new_access_token = str(new_access_token)
                    
                except TokenError:
                    # Refresh token is also invalid, user needs to login again
                    pass
        
        return None
    
    def get_refresh_token_from_request(self, request):
        """
        Try to get refresh token from request body, cookies, or headers
        """
        # Try to get from request body
        if hasattr(request, 'body') and request.body:
            try:
                body_data = json.loads(request.body)
                if 'refresh' in body_data:
                    return body_data['refresh']
            except:
                pass
        
        # Try to get from cookies
        refresh_token = request.COOKIES.get('refresh_token')
        if refresh_token:
            return refresh_token
        
        # Try to get from custom header
        refresh_token = request.META.get('HTTP_X_REFRESH_TOKEN')
        if refresh_token:
            return refresh_token
        
        return None

    def process_response(self, request, response):
        """
        Add new access token to response headers if token was refreshed
        """
        if hasattr(request, 'token_refreshed') and request.token_refreshed:
            response['X-New-Access-Token'] = request.new_access_token
            response['X-Token-Refreshed'] = 'true'
        
        return response
