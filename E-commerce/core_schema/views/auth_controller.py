"""
Authentication Controller
Handles authentication operations like login, logout, token refresh
"""

import os
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth.hashers import check_password
from supabase import create_client, Client
from decouple import config
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from datetime import datetime

# Initialize Supabase client
SUPABASE_URL = str(config('Database_Url'))
SUPABASE_KEY = str(config('Database_key'))

# Ensure environment variables are loaded
if not SUPABASE_URL or not SUPABASE_KEY or SUPABASE_URL == 'None' or SUPABASE_KEY == 'None':
    raise ValueError("Missing Supabase configuration. Please check your .env file.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@api_view(['POST'])
@permission_classes([AllowAny])
def user_login(request):
    """
    User login controller using Supabase client
    Supports both email and username login
    Returns JWT tokens
    """
    data = request.data
    
    # Check if user is already logged in
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
        try:
            # Try to decode the token
            jwt_auth = JWTAuthentication()
            validated_token = jwt_auth.get_validated_token(token)
            user_id = validated_token.get('user_id')
            if user_id:
                return Response({
                    'message': 'User is already logged in',
                    'user_id': user_id
                }, status=status.HTTP_200_OK)
        except (InvalidToken, TokenError):
            # Token is invalid, continue with login
            pass
    
    # Validate required fields
    required_fields = ['email', 'password']  # email can also be username
    if not all(field in data for field in required_fields):
        return Response({
            'error': f'Required fields: {", ".join(required_fields)}'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        email_or_username = data.get('email')
        password = data.get('password')
        
        # Check if input contains @ (email) or not (username)
        if '@' in email_or_username:
            # Login with email
            user_result = supabase.table('auth_user').select('*').eq('email', email_or_username).execute()
        else:
            # Login with username
            user_result = supabase.table('auth_user').select('*').eq('username', email_or_username).execute()
        
        if not user_result.data:
            return Response({
                'error': 'Invalid credentials'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        user = user_result.data[0]
        
        # Check password
        if not check_password(password, user.get('password')):
            return Response({
                'error': 'Invalid credentials'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Check if user is active
        if not user.get('is_active', True):
            return Response({
                'error': 'Account is deactivated'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Update last login in Supabase
        current_time = datetime.now().isoformat()
        supabase.table('auth_user').update({
            'last_login': current_time
        }).eq('id', user.get('id')).execute()
        
        # Generate JWT tokens with custom claims
        refresh = RefreshToken()
        refresh['user_id'] = user.get('id')
        refresh['username'] = user.get('username')
        refresh['email'] = user.get('email')
        refresh['is_staff'] = user.get('is_staff', False)
        refresh['is_superuser'] = user.get('is_superuser', False)
        refresh['is_active'] = user.get('is_active', True)
        
        access_token = refresh.access_token
        # Add same claims to access token
        access_token['user_id'] = user.get('id')
        access_token['username'] = user.get('username')
        access_token['email'] = user.get('email')
        access_token['is_staff'] = user.get('is_staff', False)
        access_token['is_superuser'] = user.get('is_superuser', False)
        access_token['is_active'] = user.get('is_active', True)
        
        return Response({
            'message': 'Login successful',
            'user': {
                'id': user.get('id'),
                'username': user.get('username'),
                'email': user.get('email'),
                'first_name': user.get('first_name'),
                'last_name': user.get('last_name'),
                'is_staff': user.get('is_staff'),
                'is_superuser': user.get('is_superuser'),
                'is_active': user.get('is_active'),
                'last_login': current_time
            },
            'tokens': {
                'access': str(access_token),
                'refresh': str(refresh)
            }
        }, status=status.HTTP_200_OK)
            
    except Exception as e:
        return Response({
            'error': f'An error occurred: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_token(request):
    """
    Refresh JWT access token using refresh token
    Enhanced with automatic refresh capabilities
    """
    data = request.data
    
    if 'refresh' not in data:
        return Response({
            'error': 'Refresh token is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        refresh_token = RefreshToken(data['refresh'])
        access_token = refresh_token.access_token
        
        # Add custom claims to new access token
        user_id = refresh_token.get('user_id')
        if user_id:
            # Get updated user data from Supabase
            user_result = supabase.table('auth_user').select('*').eq('id', user_id).execute()
            if user_result.data:
                user = user_result.data[0]
                
                # Check if user is still active
                if not user.get('is_active', True):
                    return Response({
                        'error': 'Account is deactivated'
                    }, status=status.HTTP_401_UNAUTHORIZED)
                
                access_token['user_id'] = user.get('id')
                access_token['username'] = user.get('username')
                access_token['email'] = user.get('email')
                access_token['is_staff'] = user.get('is_staff', False)
                access_token['is_superuser'] = user.get('is_superuser', False)
                access_token['is_active'] = user.get('is_active', True)
                
                return Response({
                    'access': str(access_token),
                    'user': {
                        'id': user.get('id'),
                        'username': user.get('username'),
                        'email': user.get('email'),
                        'is_staff': user.get('is_staff'),
                        'is_superuser': user.get('is_superuser'),
                        'is_active': user.get('is_active')
                    }
                }, status=status.HTTP_200_OK)
        
        return Response({
            'access': str(access_token)
        }, status=status.HTTP_200_OK)
        
    except TokenError as e:
        return Response({
            'error': 'Invalid or expired refresh token. Please login again.'
        }, status=status.HTTP_401_UNAUTHORIZED)
    except Exception as e:
        return Response({
            'error': f'An error occurred: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
def check_token_status(request):
    """
    Check if access token is valid and auto-refresh if needed
    """
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return Response({
            'valid': False,
            'message': 'No token provided'
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    access_token = auth_header.split(' ')[1]
    
    try:
        # Try to validate the current access token
        jwt_auth = JWTAuthentication()
        validated_token = jwt_auth.get_validated_token(access_token)
        
        return Response({
            'valid': True,
            'user_id': validated_token.get('user_id'),
            'username': validated_token.get('username'),
            'email': validated_token.get('email'),
            'expires_at': validated_token.get('exp')
        }, status=status.HTTP_200_OK)
        
    except TokenError:
        # Token is invalid/expired, try to refresh
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response({
                'valid': False,
                'message': 'Access token expired and no refresh token provided'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        try:
            refresh = RefreshToken(refresh_token)
            new_access_token = refresh.access_token
            
            # Add custom claims
            user_id = refresh.get('user_id')
            if user_id:
                user_result = supabase.table('auth_user').select('*').eq('id', user_id).execute()
                if user_result.data:
                    user = user_result.data[0]
                    
                    if not user.get('is_active', True):
                        return Response({
                            'valid': False,
                            'message': 'Account is deactivated'
                        }, status=status.HTTP_401_UNAUTHORIZED)
                    
                    new_access_token['user_id'] = user.get('id')
                    new_access_token['username'] = user.get('username')
                    new_access_token['email'] = user.get('email')
                    new_access_token['is_staff'] = user.get('is_staff', False)
                    new_access_token['is_superuser'] = user.get('is_superuser', False)
                    new_access_token['is_active'] = user.get('is_active', True)
            
            return Response({
                'valid': True,
                'refreshed': True,
                'access': str(new_access_token),
                'user_id': new_access_token.get('user_id'),
                'username': new_access_token.get('username'),
                'email': new_access_token.get('email'),
                'expires_at': new_access_token.get('exp')
            }, status=status.HTTP_200_OK)
            
        except TokenError:
            return Response({
                'valid': False,
                'message': 'Both access and refresh tokens are invalid. Please login again.'
            }, status=status.HTTP_401_UNAUTHORIZED)
    
    except Exception as e:
        return Response({
            'valid': False,
            'message': f'An error occurred: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def user_logout(request):
    """
    Logout user by blacklisting the refresh token
    """
    try:
        refresh_token = request.data.get('refresh')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
            
        return Response({
            'message': 'Successfully logged out'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': f'An error occurred: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
