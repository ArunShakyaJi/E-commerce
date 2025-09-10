from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from ..models.user import User
import re

class UserSerializer(serializers.ModelSerializer):
    role_name = serializers.CharField(source='role.role_name', read_only=True)
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'password', 'confirm_password', 'email', 'role', 'role_name']
        read_only_fields = ['id']
        extra_kwargs = {
            'password': {'write_only': True},
        }
    
    def validate_username(self, value):
        """
        Validate username is unique and follows proper format
        """
        if self.instance and self.instance.username == value:
            return value
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already exists")
        if len(value) < 3:
            raise serializers.ValidationError("Username must be at least 3 characters long")
        if not re.match(r'^[a-zA-Z0-9_]+$', value):
            raise serializers.ValidationError("Username can only contain letters, numbers, and underscores")
        return value
    
    def validate_email(self, value):
        """
        Validate email is unique
        """
        if self.instance and self.instance.email == value:
            return value
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists")
        return value
    
    def validate_password(self, value):
        """
        Validate password strength
        """
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long")
        if not re.search(r'[A-Z]', value):
            raise serializers.ValidationError("Password must contain at least one uppercase letter")
        if not re.search(r'[a-z]', value):
            raise serializers.ValidationError("Password must contain at least one lowercase letter")
        if not re.search(r'\d', value):
            raise serializers.ValidationError("Password must contain at least one number")
        return value
    
    def validate(self, data):
        """
        Validate password confirmation
        """
        if 'password' in data and 'confirm_password' in data:
            if data['password'] != data['confirm_password']:
                raise serializers.ValidationError("Passwords do not match")
        return data
    
    def create(self, validated_data):
        """
        Create user with hashed password
        """
        validated_data.pop('confirm_password', None)
        validated_data['password'] = make_password(validated_data['password'])
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        """
        Update user with hashed password if password is provided
        """
        validated_data.pop('confirm_password', None)
        if 'password' in validated_data:
            validated_data['password'] = make_password(validated_data['password'])
        return super().update(instance, validated_data)
