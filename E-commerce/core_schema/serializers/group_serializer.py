from rest_framework import serializers
from ..models.group import CustomGroup
from .permission_serializer import PermissionSerializer

class CustomGroupSerializer(serializers.ModelSerializer):
    permissions_details = PermissionSerializer(source='permissions', many=True, read_only=True)
    permission_names = serializers.StringRelatedField(source='permissions', many=True, read_only=True)
    
    class Meta:
        model = CustomGroup
        fields = ['id', 'group_name', 'permissions', 'permissions_details', 'permission_names', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_group_name(self, value):
        """
        Validate group name is unique and properly formatted
        """
        if self.instance and self.instance.group_name == value:
            return value
        if CustomGroup.objects.filter(group_name=value).exists():
            raise serializers.ValidationError("Group name already exists")
        if len(value.strip()) < 2:
            raise serializers.ValidationError("Group name must be at least 2 characters long")
        return value.strip()
