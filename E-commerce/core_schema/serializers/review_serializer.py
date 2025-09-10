from rest_framework import serializers
from ..models.review import Review

class ReviewSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user_id.username', read_only=True)
    product_name = serializers.CharField(source='product_id.name', read_only=True)
    
    class Meta:
        model = Review
        fields = ['id', 'review', 'rating', 'user_id', 'user_username', 'product_id', 'product_name', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_rating(self, value):
        """
        Validate rating is between 1 and 5
        """
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5")
        return value
    
    def validate_review(self, value):
        """
        Validate review text is not empty
        """
        if not value or not value.strip():
            raise serializers.ValidationError("Review text cannot be empty")
        if len(value) < 10:
            raise serializers.ValidationError("Review must be at least 10 characters long")
        return value
