"""
Test the product creation workflow with image upload

This script demonstrates the two workflows available:

1. Superuser Workflow (Recommended):
   POST /api/products/create-with-image/
   - Upload image file directly
   - Automatic Cloudinary upload
   - Automatic image metadata save
   - Product creation with image_id

2. Frontend Workflow:
   Step 1: POST /api/upload-image/ → get image_id
   Step 2: POST /api/products/ with image_id

3. Legacy Workflow:
   POST /api/products/ with image_url
"""

# Example usage for the superuser workflow:

import requests

def test_superuser_product_creation():
    """
    Test the complete superuser workflow
    """
    
    # 1. Login to get JWT token
    login_data = {
        'username': 'your_superuser_username',
        'password': 'your_password'
    }
    
    login_response = requests.post(
        'http://127.0.0.1:8000/api/login/',
        data=login_data
    )
    
    if login_response.status_code == 200:
        token = login_response.json()['access_token']
        
        # 2. Create product with image in one request
        headers = {
            'Authorization': f'Bearer {token}'
        }
        
        # Prepare form data
        files = {
            'image': open('path/to/your/image.jpg', 'rb')  # Replace with actual image path
        }
        
        data = {
            'name': 'Test Product with Image',
            'description': 'This is a test product created via superuser workflow',
            'price': 29.99,
            'stock': 100,
            'category_id': 1,  # Replace with actual category ID
            'image_name': 'test_product_image.jpg',
            'alt_text': 'Test product image'
        }
        
        # 3. Make the request
        response = requests.post(
            'http://127.0.0.1:8000/api/products/create-with-image/',
            headers=headers,
            files=files,
            data=data
        )
        
        print("Response Status:", response.status_code)
        print("Response Data:", response.json())
        
        files['image'].close()
    
    else:
        print("Login failed:", login_response.json())

def test_frontend_workflow():
    """
    Test the frontend workflow (two-step process)
    """
    
    # Step 1: Upload image first
    files = {
        'image': open('path/to/your/image.jpg', 'rb')  # Replace with actual image path
    }
    
    data = {
        'image_name': 'frontend_test_image.jpg',
        'alt_text': 'Frontend uploaded image'
    }
    
    # Upload image
    image_response = requests.post(
        'http://127.0.0.1:8000/api/upload-image/',
        files=files,
        data=data
    )
    
    print("Image Upload Response:", image_response.status_code)
    print("Image Upload Data:", image_response.json())
    
    if image_response.status_code == 201:
        image_id = image_response.json()['image']['id']
        
        # Step 2: Create product with image_id
        # (Need to login first for this step)
        login_data = {
            'username': 'your_username',
            'password': 'your_password'
        }
        
        login_response = requests.post(
            'http://127.0.0.1:8000/api/login/',
            data=login_data
        )
        
        if login_response.status_code == 200:
            token = login_response.json()['access_token']
            
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            product_data = {
                'name': 'Frontend Workflow Product',
                'description': 'Product created using frontend workflow',
                'price': 39.99,
                'stock': 50,
                'category_id': 1,  # Replace with actual category ID
                'image_id': image_id  # Use the uploaded image ID
            }
            
            product_response = requests.post(
                'http://127.0.0.1:8000/api/products/',
                headers=headers,
                json=product_data
            )
            
            print("Product Creation Response:", product_response.status_code)
            print("Product Creation Data:", product_response.json())
    
    files['image'].close()

if __name__ == "__main__":
    print("=== Testing Product Creation Workflows ===")
    print("\n1. Testing Superuser Workflow:")
    # test_superuser_product_creation()
    
    print("\n2. Testing Frontend Workflow:")
    # test_frontend_workflow()
    
    print("\nUncomment the function calls above and update the credentials/paths to test")
