from rest_framework import serializers
from ..models.cart import Cart
from ..models.product import Product

class CartSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product_id.name', read_only=True)
    product_price = serializers.DecimalField(source='product_id.price', max_digits=10, decimal_places=2, read_only=True)
    product_stock = serializers.IntegerField(source='product_id.stock', read_only=True)
    total_price = serializers.SerializerMethodField()
    
    class Meta:
        model = Cart
        fields = ['id', 'user_id', 'product_id', 'quantity', 'price', 'product_name', 'product_price', 'product_stock', 'total_price', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at', 'price']
    
    def get_total_price(self, obj):
        """
        Calculate total price for this cart item
        """
        return float(obj.price) * obj.quantity
    
    def validate_quantity(self, value):
        """
        Validate quantity is positive
        """
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than 0")
        return value
    
    def validate(self, data):
        """
        Check product stock availability
        """
        product = data.get('product_id')
        quantity = data.get('quantity')
        
        if product and quantity:
            if product.stock < quantity:
                raise serializers.ValidationError("Insufficient stock available")
        
        return data
    
    def create(self, validated_data):
        """
        Set price from product when creating cart item
        """
        product = validated_data['product_id']
        validated_data['price'] = product.price
        return super().create(validated_data)
