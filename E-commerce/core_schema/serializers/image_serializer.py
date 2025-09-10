from rest_framework import serializers
from ..models.Images import Images

class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Images
        fields = ['id', 'image_name', 'image_url', 'alt_text', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_image_name(self, value):
        """
        Check that image_name is unique
        """
        if self.instance and self.instance.image_name == value:
            return value
        if Images.objects.filter(image_name=value).exists():
            raise serializers.ValidationError("Image name already exists")
        return value
    
    def validate_image_url(self, value):
        """
        Check that image_url is unique
        """
        if self.instance and self.instance.image_url == value:
            return value
        if Images.objects.filter(image_url=value).exists():
            raise serializers.ValidationError("Image URL already exists")
        return value
