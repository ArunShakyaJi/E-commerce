#!/usr/bin/env python
"""
Test the exact Cloudinary configuration to match working simple test
"""
import os
import sys
import django

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

import cloudinary
import cloudinary.uploader
from decouple import config

# Load the same way as in the image_controller
CLOUDINARY_CLOUD_NAME = str(config('CLOUDINARY_CLOUD_NAME'))
CLOUDINARY_KEY = str(config('CLOUDINARY_API_KEY'))
CLOUDINARY_SECRET = str(config('CLOUDINARY_API_SECRET'))

print("=== TESTING EXACT SAME CONFIG AS WORKING ENDPOINT ===")
print(f"Cloud name: {CLOUDINARY_CLOUD_NAME}")
print(f"API Key: {CLOUDINARY_KEY[:4]}***")
print(f"API Secret: {CLOUDINARY_SECRET[:4]}***")

# Configure exactly like the working simple test
cloudinary.config( 
    cloud_name=CLOUDINARY_CLOUD_NAME, 
    api_key=CLOUDINARY_KEY, 
    api_secret=CLOUDINARY_SECRET,
    secure=True
)

# Test the configuration
try:
    # Test 1: Try to get some basic info
    print("Testing Cloudinary configuration...")
    
    # Create a temporary test file
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("This is a test file content for Cloudinary")
        temp_file_path = f.name
    
    try:
        # Test upload with same parameters as working endpoint
        upload_result = cloudinary.uploader.upload(
            temp_file_path,
            folder="test_uploads",
            resource_type="raw",
            public_id="config_test"
        )
        
        print(f"✅ Simple upload successful: {upload_result.get('secure_url')}")
        print(f"Public ID: {upload_result.get('public_id')}")
        
        # Test upload with problematic parameters from the error
        upload_result2 = cloudinary.uploader.upload(
            temp_file_path,
            folder="ecommerce/products",
            public_id="test_image_complex",
            overwrite=True,
            resource_type="raw"
        )
        
        print(f"✅ Complex upload successful: {upload_result2.get('secure_url')}")
        
    finally:
        # Clean up temp file
        import os
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
    
except Exception as e:
    print(f"❌ Error: {e}")
    
    # Try to get more info about the error
    import traceback
    print(f"Full traceback: {traceback.format_exc()}")
