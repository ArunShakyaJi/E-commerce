from rest_framework import serializers
from django.contrib.auth import get_user_model
from .product import Product
from .category import Category
from .cart import Cart
from .orders import Order
from .orderItems import OrderItems
from .review import Review
from .Images import Images
from .roles import Roles
from .group import CustomGroup
from .permission import Permission
from .productOptions import ProductOptions

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role']
        # Removed password field since it's not in the User model

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Roles
        fields = '__all__'

class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomGroup
        fields = '__all__'

class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = '__all__'

class CategorySerializer(serializers.ModelSerializer):
    user_id = UserSerializer(read_only=True)
    
    class Meta:
        model = Category
        fields = '__all__'

class ImagesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Images
        fields = '__all__'

class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    image = ImagesSerializer(read_only=True)
    user_id = UserSerializer(read_only=True)
    
    class Meta:
        model = Product
        fields = '__all__'

class ProductOptionsSerializer(serializers.ModelSerializer):
    product_id = ProductSerializer(read_only=True)
    user_id = UserSerializer(read_only=True)
    
    class Meta:
        model = ProductOptions
        fields = '__all__'

class CartSerializer(serializers.ModelSerializer):
    user_id = UserSerializer(read_only=True)
    product_id = ProductSerializer(read_only=True)
    
    class Meta:
        model = Cart
        fields = '__all__'

class OrderSerializer(serializers.ModelSerializer):
    user_id = UserSerializer(read_only=True)
    
    class Meta:
        model = Order
        fields = '__all__'

class OrderItemsSerializer(serializers.ModelSerializer):
    order_id = OrderSerializer(read_only=True)
    product_id = ProductSerializer(read_only=True)
    
    class Meta:
        model = OrderItems
        fields = '__all__'

class ReviewSerializer(serializers.ModelSerializer):
    user_id = UserSerializer(read_only=True)
    product_id = ProductSerializer(read_only=True)
    
    class Meta:
        model = Review
        fields = '__all__'
