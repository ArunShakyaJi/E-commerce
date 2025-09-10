from rest_framework import serializers
from ..models.product import Product

class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.category_name', read_only=True)
    image_url = serializers.CharField(source='image.image_url', read_only=True)
    user_username = serializers.CharField(source='user_id.username', read_only=True)
    
    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'price', 'stock', 'category', 'category_name', 'image', 'image_url', 'user_id', 'user_username', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_name(self, value):
        """
        Check that product name is unique
        """
        if self.instance and self.instance.name == value:
            return value
        if Product.objects.filter(name=value).exists():
            raise serializers.ValidationError("Product name already exists")
        return value
    
    def validate_price(self, value):
        """
        Validate price is positive
        """
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than 0")
        return value
    
    def validate_stock(self, value):
        """
        Validate stock is non-negative
        """
        if value < 0:
            raise serializers.ValidationError("Stock cannot be negative")
        return value