from rest_framework import serializers
from ..models.orders import Order

class OrderSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user_id.username', read_only=True)
    order_items = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = ['id', 'order_number', 'user_id', 'user_username', 'total_amount', 'status', 'order_items', 'created_at', 'updated_at']
        read_only_fields = ['id', 'order_number', 'total_amount', 'created_at', 'updated_at']
    
    def get_order_items(self, obj):
        """
        Get order items for this order
        """
        from .order_items_serializer import OrderItemSerializer
        order_items = obj.order_items.all()
        return OrderItemSerializer(order_items, many=True).data
    
    def validate_status(self, value):
        """
        Validate order status
        """
        valid_statuses = ['pending', 'confirmed', 'shipped', 'delivered', 'cancelled']
        if value not in valid_statuses:
            raise serializers.ValidationError(f"Status must be one of: {', '.join(valid_statuses)}")
        return value
    
    def validate_total_amount(self, value):
        """
        Validate total amount is positive
        """
        if value < 0:
            raise serializers.ValidationError("Total amount cannot be negative")
        return value
