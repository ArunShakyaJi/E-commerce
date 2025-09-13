app_name = 'core_schema'

from django.urls import path
from . import views

urlpatterns = [
    # User endpoints
    path('signup/', views.user_signup, name='user_signup'),
    path('profile/<int:user_id>/', views.user_profile, name='user_profile'),
    path('profile/update/<int:user_id>/', views.update_user_profile, name='update_user_profile'),
    
    # Authentication endpoints
    path('login/', views.user_login, name='user_login'),
    path('logout/', views.user_logout, name='user_logout'),
    path('refresh/', views.refresh_token, name='refresh_token'),
    path('check-token/', views.check_token_status, name='check_token_status'),
        
    # Product endpoints
    path('products/', views.ProductController.as_view(), name='product_list_create'),
    path('products/list/', views.product_list, name='product_list_function'),
    path('products/<int:product_id>/', views.product_detail, name='product_detail'),
    path('products/create-with-image/', views.create_product_with_image, name='create_product_with_image'),
    
    # Category endpoints
    path('categories/', views.CategoryController.as_view(), name='category_list_create'),
    path('categories/list/', views.category_list, name='category_list_function'),
    path('categories/<int:category_id>/', views.category_detail, name='category_detail'),
    
    # Cart endpoints
    path('cart/', views.CartController.as_view(), name='cart_list_create'),
    
    # Order endpoints
    path('orders/', views.OrderController.as_view(), name='order_list_create'),
    
    # Order Items endpoints
    path('order-items/', views.OrderItemsController.as_view(), name='order_items_list_create'),
    
    # Review endpoints
    path('reviews/', views.ReviewController.as_view(), name='review_list_create'),
    
    # Image endpoints
    path('upload-image/', views.upload_image, name='upload_image'),
  #  path('upload-image-test/', views.upload_image_test, name='upload_image_test'),  # Test without auth
  #  path('test-cloudinary/', views.test_cloudinary_config, name='test_cloudinary'),  # Test Cloudinary config
  #  path('debug-upload/', views.debug_file_upload, name='debug_upload'),  # Debug file upload
   # path('simple-cloudinary-test/', views.simple_cloudinary_test, name='simple_cloudinary_test'),  # Simple Cloudinary test
]