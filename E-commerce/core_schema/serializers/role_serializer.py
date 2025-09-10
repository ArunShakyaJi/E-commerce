from rest_framework import serializers
from ..models.roles import Roles

class RoleSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Roles
        fields = ['id', 'role_name', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_role_name(self, value):
        """
        Validate role name is unique and properly formatted
        """
        if self.instance and self.instance.role_name == value:
            return value
        if Roles.objects.filter(role_name=value).exists():
            raise serializers.ValidationError("Role name already exists")
        if len(value.strip()) < 2:
            raise serializers.ValidationError("Role name must be at least 2 characters long")
        return value.strip().lower()
