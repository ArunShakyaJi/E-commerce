"""
Test Supabase connection and user creation
Run this script to verify your Supabase setup is working
"""

import os
import sys
import django
from pathlib import Path

# Add the project directory to Python path
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.db import connection
from core_schema.models.user import User

def test_database_connection():
    """Test if we can connect to the database"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            print("✅ Database connection successful!")
            return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_user_creation():
    """Test if we can create a user"""
    try:
        # Try to create a test user
        test_user = User.objects.create(
            username="testuser123",
            email="test123@example.com",
            password="hashed_password_here"
        )
        print(f"✅ User created successfully: {test_user.username}")
        
        # Clean up - delete the test user
        test_user.delete()
        print("✅ Test user cleaned up")
        return True
    except Exception as e:
        print(f"❌ User creation failed: {e}")
        return False

def main():
    print("🔍 Testing Supabase Connection...")
    print("=" * 50)
    
    # Test database connection
    db_ok = test_database_connection()
    
    if db_ok:
        print("\n🔍 Testing User Model...")
        print("=" * 50)
        test_user_creation()
    else:
        print("\n⚠️  Skipping user tests due to database connection failure")
    
    print("\n📋 Next Steps:")
    print("1. Make sure your .env file has correct Supabase credentials")
    print("2. Run: python manage.py makemigrations")
    print("3. Run: python manage.py migrate")
    print("4. Test the signup endpoint")

if __name__ == "__main__":
    main()
