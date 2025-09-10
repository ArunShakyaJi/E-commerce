from rest_framework import serializers
from ..models.orderItems import OrderItems

class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product_id.name', read_only=True)
    order_number = serializers.CharField(source='order_id.order_number', read_only=True)
    total_price = serializers.SerializerMethodField()
    
    class Meta:
        model = OrderItems
        fields = ['id', 'order_id', 'order_number', 'product_id', 'product_name', 'quantity', 'price', 'total_price', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_total_price(self, obj):
        """
        Calculate total price for this order item
        """
        return obj.quantity * obj.price
    
    def validate_quantity(self, value):
        """
        Validate quantity is positive
        """
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than 0")
        return value
    
    def validate_price(self, value):
        """
        Validate price is positive
        """
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than 0")
        return value
