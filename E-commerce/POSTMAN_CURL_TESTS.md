# Postman cURL Commands for Product Creation Workflows

## Prerequisites
1. Server running at: http://127.0.0.1:8000
2. Valid user credentials (superuser for create-with-image endpoint)
3. At least one category exists in the database
4. Image file ready for upload

---

## 1. Login to Get JWT Token

### cURL Command:
```bash
curl --location 'http://127.0.0.1:8000/api/login/' \
--header 'Content-Type: application/json' \
--data '{
    "username": "your_username",
    "password": "your_password"
}'
```

### Expected Response:
```json
{
    "message": "Login successful",
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "user": {
        "id": 1,
        "username": "your_username",
        "email": "your_email@example.com"
    }
}
```

**📝 Note:** Copy the `access_token` from the response for the next requests.

---

## 2. Test Image Upload (Working Endpoint)

### cURL Command:
```bash
curl --location 'http://127.0.0.1:8000/api/upload-image/' \
--form 'image=@"/path/to/your/image.jpg"' \
--form 'image_name="test_product_image.jpg"' \
--form 'alt_text="Test product image"'
```

### Expected Response:
```json
{
    "message": "Image uploaded successfully",
    "image": {
        "id": 1,
        "image_name": "test_product_image.jpg",
        "image_url": "https://res.cloudinary.com/your-cloud/image/upload/v1234567890/test_uploads/abc123.jpg",
        "alt_text": "Test product image",
        "cloudinary_public_id": "test_uploads/abc123",
        "created_at": "2025-07-23T23:15:00.000000Z",
        "updated_at": "2025-07-23T23:15:00.000000Z"
    }
}
```

---

## 3. Superuser Workflow: Create Product with Image (Single Request)

### cURL Command:
```bash
curl --location 'http://127.0.0.1:8000/api/products/create-with-image/' \
--header 'Authorization: Bearer YOUR_JWT_TOKEN_HERE' \
--form 'image=@"/path/to/your/image.jpg"' \
--form 'name="Premium Wireless Headphones"' \
--form 'description="High-quality wireless headphones with noise cancellation"' \
--form 'price="129.99"' \
--form 'stock="50"' \
--form 'category_id="1"' \
--form 'image_name="headphones_main.jpg"' \
--form 'alt_text="Premium wireless headphones product image"'
```

### Expected Response:
```json
{
    "message": "Product created successfully with image",
    "product": {
        "id": 1,
        "name": "Premium Wireless Headphones",
        "description": "High-quality wireless headphones with noise cancellation",
        "price": "129.99",
        "stock": 50,
        "category_id": 1,
        "image_id": 2,
        "user_id": 1,
        "created_at": "2025-07-23T23:20:00.000000Z",
        "updated_at": "2025-07-23T23:20:00.000000Z",
        "category": {
            "id": 1,
            "name": "Electronics"
        },
        "image": {
            "id": 2,
            "image_name": "headphones_main.jpg",
            "image_url": "https://res.cloudinary.com/your-cloud/image/upload/v1234567890/test_uploads/xyz789.jpg",
            "alt_text": "Premium wireless headphones product image"
        },
        "user": {
            "id": 1,
            "username": "your_username",
            "email": "your_email@example.com"
        }
    },
    "workflow": {
        "step_1": "Image uploaded to Cloudinary",
        "step_2": "Image metadata saved with ID: 2",
        "step_3": "Product created with image_id: 2"
    }
}
```

---

## 4. Frontend Workflow: Step 1 - Upload Image First

### cURL Command:
```bash
curl --location 'http://127.0.0.1:8000/api/upload-image/' \
--form 'image=@"/path/to/your/image.jpg"' \
--form 'image_name="smartphone_image.jpg"' \
--form 'alt_text="Smartphone product image"'
```

### Expected Response:
```json
{
    "message": "Image uploaded successfully",
    "image": {
        "id": 3,
        "image_name": "smartphone_image.jpg",
        "image_url": "https://res.cloudinary.com/your-cloud/image/upload/v1234567890/test_uploads/def456.jpg",
        "alt_text": "Smartphone product image",
        "cloudinary_public_id": "test_uploads/def456",
        "created_at": "2025-07-23T23:25:00.000000Z",
        "updated_at": "2025-07-23T23:25:00.000000Z"
    }
}
```

**📝 Note:** Copy the `image.id` (e.g., `3`) for the next step.

---

## 5. Frontend Workflow: Step 2 - Create Product with Image ID

### cURL Command:
```bash
curl --location 'http://127.0.0.1:8000/api/products/' \
--header 'Authorization: Bearer YOUR_JWT_TOKEN_HERE' \
--header 'Content-Type: application/json' \
--data '{
    "name": "Latest Smartphone",
    "description": "Feature-rich smartphone with advanced camera",
    "price": 699.99,
    "stock": 25,
    "category_id": 1,
    "image_id": 3
}'
```

### Expected Response:
```json
{
    "message": "Product created successfully",
    "product": {
        "id": 2,
        "name": "Latest Smartphone",
        "description": "Feature-rich smartphone with advanced camera",
        "price": "699.99",
        "stock": 25,
        "category_id": 1,
        "image_id": 3,
        "user_id": 1,
        "created_at": "2025-07-23T23:30:00.000000Z",
        "updated_at": "2025-07-23T23:30:00.000000Z",
        "category": {
            "id": 1,
            "name": "Electronics"
        },
        "image": {
            "id": 3,
            "image_name": "smartphone_image.jpg",
            "image_url": "https://res.cloudinary.com/your-cloud/image/upload/v1234567890/test_uploads/def456.jpg",
            "alt_text": "Smartphone product image"
        },
        "user": {
            "id": 1,
            "username": "your_username",
            "email": "your_email@example.com"
        }
    }
}
```

---

## 6. Legacy Workflow: Create Product with Image URL

### cURL Command:
```bash
curl --location 'http://127.0.0.1:8000/api/products/' \
--header 'Authorization: Bearer YOUR_JWT_TOKEN_HERE' \
--header 'Content-Type: application/json' \
--data '{
    "name": "Gaming Laptop",
    "description": "High-performance gaming laptop",
    "price": 1299.99,
    "stock": 10,
    "category_id": 1,
    "image_url": "https://res.cloudinary.com/your-cloud/image/upload/v1234567890/test_uploads/gaming_laptop.jpg",
    "image_name": "gaming_laptop.jpg",
    "alt_text": "Gaming laptop product image"
}'
```

---

## 7. Test Endpoints for Debugging

### Test Simple Cloudinary Upload:
```bash
curl --location 'http://127.0.0.1:8000/api/simple-cloudinary-test/' \
--form 'image=@"/path/to/your/image.jpg"'
```

### Test Cloudinary Configuration:
```bash
curl --location 'http://127.0.0.1:8000/api/test-cloudinary/'
```

### Get All Products:
```bash
curl --location 'http://127.0.0.1:8000/api/products/list/'
```

---

## Important Notes:

### 🔑 Authentication Requirements:
- `/api/upload-image/` - No authentication (temporarily disabled)
- `/api/products/create-with-image/` - Requires superuser JWT token
- `/api/products/` - Requires authenticated user JWT token

### 📁 File Path Format:
- **Windows**: `@"C:/path/to/your/image.jpg"`
- **macOS/Linux**: `@"/path/to/your/image.jpg"`

### 🏷️ Supported Image Formats:
- JPG, JPEG, PNG, GIF, WebP

### 📊 Required Fields:
- `name` (string, unique)
- `price` (decimal)
- `category_id` (integer, must exist)

### 🎯 Optional Fields:
- `description` (string)
- `stock` (integer, default: 0)
- `image_name` (string)
- `alt_text` (string)

---

## Quick Test - Updated for Signature Fix:

### Test the working simple upload first:
```bash
curl --location 'http://127.0.0.1:8000/api/simple-cloudinary-test/' \
--form 'image=@"C:/path/to/your/image.jpg"'
```

### Then test the superuser workflow (with fresh Cloudinary config):
```bash
curl --location 'http://127.0.0.1:8000/api/products/create-with-image/' \
--header 'Authorization: Bearer YOUR_JWT_TOKEN_HERE' \
--form 'image=@"C:/path/to/your/image.jpg"' \
--form 'name="Test Product Fixed"' \
--form 'description="Testing with fixed Cloudinary config"' \
--form 'price="29.99"' \
--form 'stock="100"' \
--form 'category_id="1"' \
--form 'image_name="test_fixed.jpg"' \
--form 'alt_text="Fixed test image"'
```

### If you still get signature errors, try this debug approach:
```bash
# Test authenticated image upload first
curl --location 'http://127.0.0.1:8000/api/upload-image/' \
--header 'Authorization: Bearer YOUR_JWT_TOKEN_HERE' \
--form 'image=@"C:/path/to/your/image.jpg"' \
--form 'image_name="debug_test.jpg"' \
--form 'alt_text="Debug test"'
```

## Quick Test Sequence:

1. **Login** → Get JWT token
2. **Test simple upload** → Verify Cloudinary works
3. **Test superuser workflow** → Complete product creation
4. **Verify** → Check products list

Replace `YOUR_JWT_TOKEN_HERE` with the actual token from step 1!
