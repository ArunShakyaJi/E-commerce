from rest_framework import serializers
from ..models.category import Category

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'category_name', 'description', 'user_id', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_category_name(self, value):
        """
        Check that category_name is unique
        """
        if self.instance and self.instance.category_name == value:
            return value
        if Category.objects.filter(category_name=value).exists():
            raise serializers.ValidationError("Category name already exists")
        return value
