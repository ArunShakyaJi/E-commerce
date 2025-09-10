#!/bin/bash

# Quick Test Script for Product Creation Workflows
# Make sure to update the variables below before running

# Configuration
SERVER_URL="http://127.0.0.1:8000"
USERNAME="your_username"  # Update this
PASSWORD="your_password"  # Update this
IMAGE_PATH="/path/to/your/image.jpg"  # Update this
CATEGORY_ID="1"  # Update this if needed

echo "=== Product Creation Workflow Tests ==="

# Step 1: Login and get JWT token
echo "1. Logging in..."
LOGIN_RESPONSE=$(curl -s --location "${SERVER_URL}/api/login/" \
  --header 'Content-Type: application/json' \
  --data "{
    \"username\": \"${USERNAME}\",
    \"password\": \"${PASSWORD}\"
  }")

echo "Login Response: $LOGIN_RESPONSE"

# Extract token (requires jq - install with: brew install jq or apt-get install jq)
if command -v jq &> /dev/null; then
    TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.access_token')
    echo "JWT Token: ${TOKEN:0:50}..."
else
    echo "Please install 'jq' to automatically extract token, or copy it manually from the response above"
    echo "Then set: TOKEN='your_jwt_token_here'"
    read -p "Press enter to continue after setting TOKEN variable..."
fi

# Step 2: Test simple image upload (no auth needed)
echo -e "\n2. Testing simple image upload..."
curl --location "${SERVER_URL}/api/simple-cloudinary-test/" \
  --form "image=@\"${IMAGE_PATH}\""

# Step 3: Test authenticated image upload
echo -e "\n3. Testing authenticated image upload..."
curl --location "${SERVER_URL}/api/upload-image/" \
  --form "image=@\"${IMAGE_PATH}\"" \
  --form 'image_name="test_image.jpg"' \
  --form 'alt_text="Test image"'

# Step 4: Test superuser product creation workflow
echo -e "\n4. Testing superuser product creation with image..."
curl --location "${SERVER_URL}/api/products/create-with-image/" \
  --header "Authorization: Bearer ${TOKEN}" \
  --form "image=@\"${IMAGE_PATH}\"" \
  --form 'name="Test Product from Script"' \
  --form 'description="Product created via test script"' \
  --form 'price="99.99"' \
  --form 'stock="20"' \
  --form "category_id=\"${CATEGORY_ID}\"" \
  --form 'image_name="script_test_image.jpg"' \
  --form 'alt_text="Test product image from script"'

echo -e "\n=== Tests Complete ==="
