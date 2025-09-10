from rest_framework import serializers
from ..models.productOptions import ProductOptions

class ProductOptionsSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product_id.name', read_only=True)
    user_username = serializers.CharField(source='user_id.username', read_only=True)
    
    class Meta:
        model = ProductOptions
        fields = ['id', 'option_name', 'option_price', 'option_description', 'stock', 'product_id', 'product_name', 'user_id', 'user_username', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_option_name(self, value):
        """
        Validate option name is not empty
        """
        if not value or not value.strip():
            raise serializers.ValidationError("Option name cannot be empty")
        return value.strip()
    
    def validate_option_price(self, value):
        """
        Validate option price is positive
        """
        if value <= 0:
            raise serializers.ValidationError("Option price must be greater than 0")
        return value
    
    def validate_stock(self, value):
        """
        Validate stock is non-negative
        """
        if value < 0:
            raise serializers.ValidationError("Stock cannot be negative")
        return value
