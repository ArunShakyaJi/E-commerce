from rest_framework import serializers
from ..models.permission import Permission

class PermissionSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Permission
        fields = ['id', 'permission_name', 'type', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_permission_name(self, value):
        """
        Validate permission name is unique and properly formatted
        """
        if self.instance and self.instance.permission_name == value:
            return value
        if Permission.objects.filter(permission_name=value).exists():
            raise serializers.ValidationError("Permission name already exists")
        if len(value.strip()) < 3:
            raise serializers.ValidationError("Permission name must be at least 3 characters long")
        return value.strip()
