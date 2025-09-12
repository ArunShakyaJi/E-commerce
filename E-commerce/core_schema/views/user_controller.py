"""
User Controller
Handles user-related operations like signup, profile management
"""

import os
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth.hashers import make_password
from supabase import create_client, Client
from decouple import config
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from ..serializers.user_serializer import UserSerializer

# Initialize Supabase client
SUPABASE_URL = str(config('Database_Url'))
SUPABASE_KEY = str(config('Database_key'))

# Ensure environment variables are loaded
if not SUPABASE_URL or not SUPABASE_KEY or SUPABASE_URL == 'None' or SUPABASE_KEY == 'None':
    raise ValueError("Missing Supabase configuration. Please check your .env file.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@api_view(['POST'])
@permission_classes([AllowAny])
def user_signup(request):
    """
    User signup controller using Supabase client
    Expects: username, email, password, first_name, last_name, etc.
    """
    data = request.data
    
    # Validate required fields
    required_fields = ['username', 'email', 'password']
    if not all(field in data for field in required_fields):
        return Response({
            'error': f'Required fields: {", ".join(required_fields)}'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Basic validation
    if len(data['password']) < 8:
        return Response({
            'error': 'Password must be at least 8 characters long.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Check if username or email already exists
        username_check = supabase.table('auth_user').select('id').eq('username', data['username']).execute()
        email_check = supabase.table('auth_user').select('id').eq('email', data['email']).execute()
        
        if username_check.data:
            return Response({
                'error': 'Username already exists'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if email_check.data:
            return Response({
                'error': 'Email already exists'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Hash the password
        hashed_password = make_password(data['password'])
        
        # Prepare user data for insertion
        user_data = {
            'username': data['username'],
            'email': data['email'],
            'password': hashed_password,
            'first_name': data.get('first_name', ''),
            'last_name': data.get('last_name', ''),
            'is_superuser': data.get('is_superuser', False),
            'is_staff': data.get('is_staff', False),
            'is_active': data.get('is_active', True),
            'date_joined': data.get('date_joined'),
            'last_login': data.get('last_login')
        }
        
        # Remove None values
        user_data = {k: v for k, v in user_data.items() if v is not None}
        
        # Insert user into Supabase
        result = supabase.table('auth_user').insert(user_data).execute()
        
        if result.data:
            user = result.data[0]
            return Response({
                'message': 'User created successfully',
                'user': {
                    'id': user.get('id'),
                    'username': user.get('username'),
                    'email': user.get('email'),
                    'first_name': user.get('first_name'),
                    'last_name': user.get('last_name'),
                    'is_superuser': user.get('is_superuser'),
                    'is_staff': user.get('is_staff'),
                    'is_active': user.get('is_active'),
                    'date_joined': user.get('date_joined'),
                    'last_login': user.get('last_login')
                }
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'error': 'Failed to create user'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        return Response({
            'error': f'An error occurred: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_profile(request, user_id):
    """
    Get user profile by user_id from URL, with token validation
    """
    try:
        # Validate JWT token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return Response({'error': 'Authorization header missing'}, status=status.HTTP_401_UNAUTHORIZED)
        token = auth_header.split(' ')[1]
        jwt_auth = JWTAuthentication()
        jwt_auth.get_validated_token(token)  # Just validate, don't extract user_id

        # Get user data from Supabase by user_id from URL
        user_result = supabase.table('auth_user').select('*').eq('id', user_id).execute()
        if not user_result.data:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        user = user_result.data[0]
        return Response({'user': {
            'id': user.get('id'),
            'username': user.get('username'),
            'email': user.get('email'),
            'first_name': user.get('first_name'),
            'last_name': user.get('last_name'),
            'is_staff': user.get('is_staff'),
            'is_superuser': user.get('is_superuser'),
            'is_active': user.get('is_active'),
            'date_joined': user.get('date_joined'),
            'last_login': user.get('last_login')
        }}, status=status.HTTP_200_OK)
    except (InvalidToken, TokenError):
        return Response({'error': 'Invalid or expired token'}, status=status.HTTP_401_UNAUTHORIZED)
    except Exception as e:
        return Response({'error': f'An error occurred: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    """
    Get current user profile from token
    """

@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_user_profile(request , user_id):
    """
    Update current user profile
    """
    try:
        # Get user ID from JWT token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return Response({
                'error': 'Authorization header missing'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        token = auth_header.split(' ')[1]
        jwt_auth = JWTAuthentication()
        validated_token = jwt_auth.get_validated_token(token)
        user_id = user_id
        
        if not user_id:
            return Response({
                'error': 'Invalid token'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Get current user data
        user_result = supabase.table('auth_user').select('*').eq('id', user_id).execute()
        
        if not user_result.data:
            return Response({
                'error': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Prepare update data
        data = request.data
        update_data = {}
        
        # Allow updating these fields
        updatable_fields = ['first_name', 'last_name', 'email']
        
        for field in updatable_fields:
            if field in data:
                update_data[field] = data[field]
        
        # Check if email is being updated and if it's unique
        if 'email' in update_data:
            current_user = user_result.data[0]
            if update_data['email'] != current_user.get('email'):
                email_check = supabase.table('auth_user').select('id').eq('email', update_data['email']).neq('id', user_id).execute()
                if email_check.data:
                    return Response({
                        'error': 'Email already exists'
                    }, status=status.HTTP_400_BAD_REQUEST)
        
        # Update user in Supabase
        if update_data:
            result = supabase.table('auth_user').update(update_data).eq('id', user_id).execute()
            
            if result.data:
                updated_user = result.data[0]
                return Response({
                    'message': 'Profile updated successfully',
                    'user': {
                        'id': updated_user.get('id'),
                        'username': updated_user.get('username'),
                        'email': updated_user.get('email'),
                        'first_name': updated_user.get('first_name'),
                        'last_name': updated_user.get('last_name'),
                        'is_staff': updated_user.get('is_staff'),
                        'is_superuser': updated_user.get('is_superuser'),
                        'is_active': updated_user.get('is_active'),
                        'date_joined': updated_user.get('date_joined'),
                        'last_login': updated_user.get('last_login')
                    }
                }, status=status.HTTP_200_OK)
        
        return Response({
            'message': 'No changes made'
        }, status=status.HTTP_200_OK)
        
    except (InvalidToken, TokenError):
        return Response({
            'error': 'Invalid or expired token'
        }, status=status.HTTP_401_UNAUTHORIZED)
    except Exception as e:
        return Response({
            'error': f'An error occurred: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_user_profile(request):
    pass


