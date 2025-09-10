# Views package for core_schema
# This package contains organized controllers for different functionalities

from .user_controller import user_signup, user_profile, update_user_profile
from .auth_controller import user_login, user_logout, refresh_token, check_token_status
from .product_controller import ProductController, product_list, product_detail, create_product_with_image
from .category_controller import CategoryController, category_list, category_detail
from .cart_controller import CartController
from .order_controller import OrderController
from .order_items_controller import OrderItemsController
from .review_controller import ReviewController
from .image_controller import upload_image, upload_image_test, test_cloudinary_config, debug_file_upload, simple_cloudinary_test

__all__ = [
    # User related views
    'user_signup',
    'user_profile',
    'update_user_profile',
    
    # Auth related views
    'user_login',
    'user_logout',
    'refresh_token',
    'check_token_status',
    
    # Product related views
    'ProductController',
    'product_list',
    'product_detail',
    'create_product_with_image',
    
    # Category related views
    'CategoryController',
    'category_list',
    'category_detail',
    
    # Cart related views
    'CartController',
    
    # Order related views
    'OrderController',
    'OrderItemsController',
    
    # Review related views
    'ReviewController',
    
    # Image related views
    'upload_image',
    'upload_image_test',
    'test_cloudinary_config',
    'debug_file_upload',
    'simple_cloudinary_test',
]
