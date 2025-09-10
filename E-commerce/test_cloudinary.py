# Test your Cloudinary credentials manually
import cloudinary
import cloudinary.uploader
import cloudinary.api

# Replace these with your exact credentials from Cloudinary dashboard
CLOUD_NAME = "dytofczzt"
API_KEY = "245784736911671"  # Get the exact one from dashboard
API_SECRET = "_-ZOUq0ciixyuF11eetjJ20J88g"  # Get the exact one from dashboard

# Configure Cloudinary
cloudinary.config(
    cloud_name=CLOUD_NAME,
    api_key=API_KEY,
    api_secret=API_SECRET,
    secure=True
)

try:
    # Test the connection
    result = cloudinary.api.ping()
    print("✅ Cloudinary connection successful!")
    print(f"Result: {result}")
    
    # Test a simple upload
    # Replace 'path/to/test/image.jpg' with an actual image file path
    # upload_result = cloudinary.uploader.upload("path/to/test/image.jpg")
    # print(f"Upload successful: {upload_result['secure_url']}")
    
except Exception as e:
    print(f"❌ Cloudinary error: {e}")
    print("\nTroubleshooting:")
    print("1. Check your credentials in Cloudinary dashboard")
    print("2. Make sure API key and secret are exactly as shown")
    print("3. Ensure your Cloudinary account is active")
