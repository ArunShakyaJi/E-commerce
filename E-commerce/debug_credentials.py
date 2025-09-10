#!/usr/bin/env python
"""
Debug the exact credential loading to match working endpoint
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

from decouple import config

# Load exactly like in image_controller.py
CLOUDINARY_CLOUD_NAME = str(config('CLOUDINARY_CLOUD_NAME'))
CLOUDINARY_URL = str(config('CLOUDINARY_URL'))
CLOUDINARY_KEY = str(config('CLOUDINARY_API_KEY'))
CLOUDINARY_SECRET = str(config('CLOUDINARY_API_SECRET'))

print("=== EXACT CREDENTIAL DEBUG ===")
print(f"Cloud name: '{CLOUDINARY_CLOUD_NAME}' (length: {len(CLOUDINARY_CLOUD_NAME)})")
print(f"API Key: '{CLOUDINARY_KEY}' (length: {len(CLOUDINARY_KEY)})")
print(f"API Secret: '{CLOUDINARY_SECRET}' (length: {len(CLOUDINARY_SECRET)})")
print(f"URL: '{CLOUDINARY_URL}' (length: {len(CLOUDINARY_URL)})")

# Check for whitespace issues
print("\n=== WHITESPACE CHECK ===")
print(f"Cloud name starts/ends with: '{CLOUDINARY_CLOUD_NAME[0]}' / '{CLOUDINARY_CLOUD_NAME[-1]}'")
print(f"API Key starts/ends with: '{CLOUDINARY_KEY[0]}' / '{CLOUDINARY_KEY[-1]}'")
print(f"API Secret starts/ends with: '{CLOUDINARY_SECRET[0]}' / '{CLOUDINARY_SECRET[-1]}'")

# Check if values match the expected ones
expected_cloud = "dytofczzt"
expected_key = "245784736911671"
expected_secret = "_-ZOUq0ciixyuF11eetjJ20J88g"

print(f"\n=== EXACT MATCH CHECK ===")
print(f"Cloud name matches: {CLOUDINARY_CLOUD_NAME == expected_cloud}")
print(f"API Key matches: {CLOUDINARY_KEY == expected_key}")
print(f"API Secret matches: {CLOUDINARY_SECRET == expected_secret}")

if CLOUDINARY_CLOUD_NAME != expected_cloud:
    print(f"Cloud name diff: got {repr(CLOUDINARY_CLOUD_NAME)}, expected {repr(expected_cloud)}")
if CLOUDINARY_KEY != expected_key:
    print(f"API Key diff: got {repr(CLOUDINARY_KEY)}, expected {repr(expected_key)}")
if CLOUDINARY_SECRET != expected_secret:
    print(f"API Secret diff: got {repr(CLOUDINARY_SECRET)}, expected {repr(expected_secret)}")

# Test manual hardcoded config
import cloudinary
import cloudinary.uploader

print(f"\n=== TESTING HARDCODED CONFIG ===")
cloudinary.config( 
    cloud_name="dytofczzt", 
    api_key="245784736911671", 
    api_secret="_-ZOUq0ciixyuF11eetjJ20J88g",
    secure=True
)

try:
    # Create a test file
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("Test upload with hardcoded config")
        temp_file = f.name
    
    upload_result = cloudinary.uploader.upload(
        temp_file,
        folder="test_uploads",
        resource_type="auto"
    )
    
    print(f"✅ Hardcoded config upload successful: {upload_result.get('secure_url')}")
    
    # Clean up
    os.unlink(temp_file)
    
except Exception as e:
    print(f"❌ Hardcoded config failed: {e}")

# Test with loaded env vars
print(f"\n=== TESTING ENV VAR CONFIG ===")
cloudinary.config( 
    cloud_name=CLOUDINARY_CLOUD_NAME.strip(), 
    api_key=CLOUDINARY_KEY.strip(), 
    api_secret=CLOUDINARY_SECRET.strip(),
    secure=True
)

try:
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("Test upload with env var config")
        temp_file = f.name
    
    upload_result = cloudinary.uploader.upload(
        temp_file,
        folder="test_uploads",
        resource_type="auto"
    )
    
    print(f"✅ Env var config upload successful: {upload_result.get('secure_url')}")
    
    # Clean up
    os.unlink(temp_file)
    
except Exception as e:
    print(f"❌ Env var config failed: {e}")
