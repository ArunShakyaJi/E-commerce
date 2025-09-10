from rest_framework import viewsets, status, generics
from rest_framework.decorators import permission_classes, api_view
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from supabase import create_client, Client
from decouple import config
from ..models.product import Product
from ..serializers.product_serializer import ProductSerializer

# Initialize Supabase client
SUPABASE_URL = str(config('Database_Url'))
SUPABASE_KEY = str(config('Database_key'))

# Ensure environment variables are loaded
if not SUPABASE_URL or not SUPABASE_KEY or SUPABASE_URL == 'None' or SUPABASE_KEY == 'None':
    raise ValueError("Missing Supabase configuration. Please check your .env file.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)



@api_view(['GET'])
@permission_classes([AllowAny])
def product_list(request):
    """
    List all products with pagination and filtering
    """
    try:
        # Get query parameters
        page = int(request.GET.get('page', 1))
        limit = int(request.GET.get('limit', 10))
        category_id = request.GET.get('category_id')
        search = request.GET.get('search')
        
        # Calculate offset for pagination
        offset = (page - 1) * limit
        
        # Build query
        query = supabase.table('product').select('''
            *,
            category:category_id(id, name),
            image:image_id(id, image_name, image_url, alt_text),
            user:user_id(id, username, email)
        ''')
        
        # Apply filters
        if category_id:
            query = query.eq('category_id', category_id)
        
        if search:
            query = query.or_(f'name.ilike.%{search}%,description.ilike.%{search}%')
        
        # Apply pagination and ordering
        result = query.order('created_at', desc=True).range(offset, offset + limit - 1).execute()
        
        # Get total count for pagination
        count_result = supabase.table('product').select('*').execute()
        total_count = len(count_result.data) if count_result.data else 0
        
        return Response({
            'products': result.data,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total_count,
                'pages': (total_count + limit - 1) // limit,
                'has_next': offset + limit < total_count,
                'has_prev': page > 1
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': f'An error occurred while fetching products: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def product_detail(request, product_id):
    """
    Get details of a specific product
    """
    try:
        result = supabase.table('product').select('''
            *,
            category:category_id(id, name, description),
            image:image_id(id, image_name, image_url, alt_text),
            user:user_id(id, username, email, first_name, last_name)
        ''').eq('id', product_id).execute()
        
        if not result.data:
            return Response({
                'error': 'Product not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        product = result.data[0]
        
        return Response({
            'product': product
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': f'An error occurred while fetching product: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProductController(APIView):
    """
    Product Controller using Supabase for CRUD operations
    """
    
    @permission_classes([AllowAny])
    def get(self, request):
        """
        List all products with pagination and filtering
        """
        try:
            # Get query parameters
            page = int(request.GET.get('page', 1))
            limit = int(request.GET.get('limit', 10))
            category_id = request.GET.get('category_id')
            search = request.GET.get('search')
            
            # Calculate offset for pagination
            offset = (page - 1) * limit
            
            # Build query
            query = supabase.table('product').select('''
                *,
                category:category_id(id, name),
                image:image_id(id, image_name, image_url, alt_text),
                user:user_id(id, username, email)
            ''')
            
            # Apply filters
            if category_id:
                query = query.eq('category_id', category_id)
            
            if search:
                query = query.or_(f'name.ilike.%{search}%,description.ilike.%{search}%')
            
            # Apply pagination and ordering
            result = query.order('created_at', desc=True).range(offset, offset + limit - 1).execute()
            
            # Get total count for pagination
            count_result = supabase.table('product').select('*').execute()
            total_count = len(count_result.data) if count_result.data else 0
            
            return Response({
                'products': result.data,
                'pagination': {
                    'page': page,
                    'limit': limit,
                    'total': total_count,
                    'pages': (total_count + limit - 1) // limit,
                    'has_next': offset + limit < total_count,
                    'has_prev': page > 1
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': f'An error occurred while fetching products: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _handle_image_upload(self, image_file, data):
        """
        Helper method to handle image upload to Cloudinary and save metadata to Supabase
        Returns image_id on success, or Response object on error
        """
        try:
            # Import cloudinary modules and reconfigure to ensure fresh config
            import cloudinary
            import cloudinary.uploader
            from decouple import config
            
            # Force reload Cloudinary configuration
            CLOUDINARY_CLOUD_NAME = str(config('CLOUDINARY_CLOUD_NAME'))
            CLOUDINARY_KEY = str(config('CLOUDINARY_API_KEY'))
            CLOUDINARY_SECRET = str(config('CLOUDINARY_API_SECRET'))
            
            # Reconfigure Cloudinary with fresh credentials
            cloudinary.config( 
                cloud_name=CLOUDINARY_CLOUD_NAME, 
                api_key=CLOUDINARY_KEY, 
                api_secret=CLOUDINARY_SECRET,
                secure=True
            )
            
            # Reset file pointer
            if hasattr(image_file, 'seek'):
                image_file.seek(0)
            
            # Upload to Cloudinary with minimal parameters (same as working endpoint)
            upload_result = cloudinary.uploader.upload(
                image_file,
                folder="test_uploads",
                resource_type="auto"
            )
            
            # Prepare image metadata
            image_data = {
                'image_name': data.get('image_name', image_file.name),
                'image_url': upload_result.get('secure_url'),
                'alt_text': data.get('alt_text', data.get('name', 'Product image'))
            }
            
            # Save to Supabase images table
            image_result = supabase.table('images').insert(image_data).execute()
            
            if image_result.data:
                return image_result.data[0]['id']
            else:
                return Response({
                    'error': 'Failed to save image metadata to database'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            return Response({
                'error': f'Failed to upload image: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @permission_classes([IsAuthenticated])
    def post(self, request):
        """
        Create a new product with image handling
        Supports two workflows:
        1. Frontend uploads image first → provides image_id
        2. Backend handles image upload → uploads to Cloudinary and creates image record
        """
        try:
            data = request.data
            
            # Validate required fields
            required_fields = ['name', 'price', 'category_id']
            if not all(field in data for field in required_fields):
                return Response({
                    'error': f'Required fields: {", ".join(required_fields)}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Use ProductSerializer for validation
            serializer = ProductSerializer(data=data)
            if not serializer.is_valid():
                return Response({
                    'error': 'Validation failed',
                    'details': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            image_id = None
            
            # Handle image upload scenarios
            if 'image' in request.FILES:
                # Scenario 1: Backend handles image upload
                image_id = self._handle_image_upload(request.FILES['image'], data)
                if isinstance(image_id, Response):  # Error response
                    return image_id
                    
            elif 'image_id' in data and data['image_id']:
                # Scenario 2: Frontend already uploaded image, just use the ID
                image_id = int(data['image_id'])
                # Verify the image exists
                try:
                    image_check = supabase.table('images').select('id').eq('id', image_id).execute()
                    if not image_check.data:
                        return Response({
                            'error': f'Image with ID {image_id} not found'
                        }, status=status.HTTP_400_BAD_REQUEST)
                except Exception as e:
                    return Response({
                        'error': f'Failed to verify image: {str(e)}'
                    }, status=status.HTTP_400_BAD_REQUEST)
                    
            elif 'image_url' in data and data['image_url']:
                # Scenario 3: Frontend provides image_url directly (legacy support)
                image_data = {
                    'image_name': data.get('image_name', f"product_{data['name']}_image"),
                    'image_url': data['image_url'],
                    'alt_text': data.get('alt_text', data['name'])
                }
                
                try:
                    image_result = supabase.table('images').insert(image_data).execute()
                    if image_result.data:
                        image_id = image_result.data[0]['id']
                    else:
                        return Response({
                            'error': 'Failed to save image metadata'
                        }, status=status.HTTP_400_BAD_REQUEST)
                except Exception as e:
                    return Response({
                        'error': f'Failed to save image metadata: {str(e)}'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get user ID from token (assuming JWT authentication)
            user_id = request.user.id if hasattr(request.user, 'id') else None
            
            # Prepare product data
            product_data = {
                'name': data['name'],
                'description': data.get('description', ''),
                'price': float(data['price']),
                'stock': int(data.get('stock', 0)),
                'category_id': int(data['category_id']),
                'image_id': image_id,
                'user_id': user_id
            }
            
            # Insert product into Supabase
            result = supabase.table('product').insert(product_data).execute()
            
            if result.data:
                product = result.data[0]
                
                # Fetch complete product data with relationships
                complete_product = supabase.table('product').select('''
                    *,
                    category:category_id(id, category_name),
                    image:image_id(id, image_name, image_url, alt_text),
                    user:user_id(id, username, email)
                ''').eq('id', product['id']).execute()
                
                return Response({
                    'message': 'Product created successfully',
                    'product': complete_product.data[0] if complete_product.data else product
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    'error': 'Failed to create product'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except ValueError as e:
            return Response({
                'error': f'Invalid data format: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'error': f'An error occurred while creating product: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def list_products(self, request):
        """
        List all products
        """
        return self.get(request)

    def get_product(self, request, product_id):
        """
        Get details of a specific product
        """
        try:
            result = supabase.table('product').select('''
                *,
                category:category_id(id, name, description),
                image:image_id(id, image_name, image_url, alt_text),
                user:user_id(id, username, email, first_name, last_name)
            ''').eq('id', product_id).execute()
            
            if not result.data:
                return Response({
                    'error': 'Product not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            product = result.data[0]
            
            return Response({
                'product': product
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': f'An error occurred while fetching product: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def create_product(self, request):
        """
        Create a new product
        """
        return self.post(request)

    def update_product(self, request, product_id):
        """
        Update an existing product
        """
        try:
            data = request.data
            
            # Check if product exists
            existing_product = supabase.table('product').select('*').eq('id', product_id).execute()
            if not existing_product.data:
                return Response({
                    'error': 'Product not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Prepare update data
            update_data = {}
            updatable_fields = ['name', 'description', 'price', 'stock', 'category_id', 'image_id']
            
            for field in updatable_fields:
                if field in data:
                    if field in ['price']:
                        update_data[field] = float(data[field])
                    elif field in ['stock', 'category_id', 'image_id']:
                        update_data[field] = int(data[field]) if data[field] else None
                    else:
                        update_data[field] = data[field]
            
            # Check if new name already exists (if name is being updated)
            if 'name' in update_data:
                current_product = existing_product.data[0]
                if update_data['name'] != current_product.get('name'):
                    name_check = supabase.table('product').select('id').eq('name', update_data['name']).neq('id', product_id).execute()
                    if name_check.data:
                        return Response({
                            'error': 'Product name already exists'
                        }, status=status.HTTP_400_BAD_REQUEST)
            
            # Update product in Supabase
            if update_data:
                result = supabase.table('product').update(update_data).eq('id', product_id).execute()
                
                if result.data:
                    updated_product = result.data[0]
                    return Response({
                        'message': 'Product updated successfully',
                        'product': updated_product
                    }, status=status.HTTP_200_OK)
            
            return Response({
                'message': 'No changes made'
            }, status=status.HTTP_200_OK)
            
        except ValueError as e:
            return Response({
                'error': f'Invalid data format: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'error': f'An error occurred while updating product: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete_product(self, request, product_id):
        """
        Delete a product
        """
        try:
            # Check if product exists
            existing_product = supabase.table('product').select('*').eq('id', product_id).execute()
            if not existing_product.data:
                return Response({
                    'error': 'Product not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Delete product from Supabase
            result = supabase.table('product').delete().eq('id', product_id).execute()
            
            return Response({
                'message': 'Product deleted successfully'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': f'An error occurred while deleting product: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_product_with_image(request):
    """
    Superuser workflow: Create product with automatic image handling
    Steps:
    1. Upload image to Cloudinary
    2. Save image metadata to Supabase  
    3. Create product with image_id foreign key
    
    Expected data:
    - image: file upload
    - name: product name
    - description: product description (optional)
    - price: product price
    - stock: product stock (optional, default 0)
    - category_id: category foreign key
    - image_name: custom image name (optional)
    - alt_text: image alt text (optional)
    """
    try:
        # Check if user is superuser/admin
        if not (request.user.is_superuser or request.user.is_staff):
            return Response({
                'error': 'Only superusers can create products'
            }, status=status.HTTP_403_FORBIDDEN)
            
        data = request.data
        
        # Validate required fields
        required_fields = ['name', 'price', 'category_id']
        if not all(field in data for field in required_fields):
            return Response({
                'error': f'Required fields: {", ".join(required_fields)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if image is provided
        if 'image' not in request.FILES:
            return Response({
                'error': 'Image file is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        image_file = request.FILES['image']
        
        # Step 1: Upload image to Cloudinary and save to Supabase
        try:
            # Import cloudinary modules and reconfigure to ensure fresh config
            import cloudinary
            import cloudinary.uploader
            from decouple import config
            
            # Force reload Cloudinary configuration
            CLOUDINARY_CLOUD_NAME = str(config('CLOUDINARY_CLOUD_NAME'))
            CLOUDINARY_KEY = str(config('CLOUDINARY_API_KEY'))
            CLOUDINARY_SECRET = str(config('CLOUDINARY_API_SECRET'))
            
            # Reconfigure Cloudinary with fresh credentials
            cloudinary.config( 
                cloud_name=CLOUDINARY_CLOUD_NAME, 
                api_key=CLOUDINARY_KEY, 
                api_secret=CLOUDINARY_SECRET,
                secure=True
            )
            
            # Reset file pointer
            if hasattr(image_file, 'seek'):
                image_file.seek(0)
            
            # Upload to Cloudinary with minimal parameters (same as working endpoint)
            upload_result = cloudinary.uploader.upload(
                image_file,
                folder="test_uploads",
                resource_type="auto"
            )
            
            # Prepare image metadata
            image_data = {
                'image_name': data.get('image_name', image_file.name),
                'image_url': upload_result.get('secure_url'),
                'alt_text': data.get('alt_text', data['name'])
            }
            
            # Step 2: Save image metadata to Supabase
            image_result = supabase.table('images').insert(image_data).execute()
            
            if not image_result.data:
                return Response({
                    'error': 'Failed to save image metadata'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            image_id = image_result.data[0]['id']
            
        except Exception as e:
            return Response({
                'error': f'Failed to upload image: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Step 3: Create product with image_id
        try:
            # Use ProductSerializer for validation
            product_serializer_data = {
                'name': data['name'],
                'description': data.get('description', ''),
                'price': data['price'],
                'stock': data.get('stock', 0),
                'category_id': data['category_id'],
                'image_id': image_id,
                'user_id': request.user.id
            }
            
            serializer = ProductSerializer(data=product_serializer_data)
            if not serializer.is_valid():
                # If product creation fails, clean up the uploaded image
                try:
                    supabase.table('images').delete().eq('id', image_id).execute()
                except:
                    pass  # Ignore cleanup errors
                    
                return Response({
                    'error': 'Product validation failed',
                    'details': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Create product in Supabase
            product_data = {
                'name': data['name'],
                'description': data.get('description', ''),
                'price': float(data['price']),
                'stock': int(data.get('stock', 0)),
                'category_id': int(data['category_id']),
                'image_id': image_id,
                'user_id': request.user.id
            }
            
            result = supabase.table('product').insert(product_data).execute()
            
            if result.data:
                created_product = result.data[0]
                
                # Fetch the complete product data with relationships
                complete_product = supabase.table('product').select('''
                    *,
                    category:category_id(id, name),
                    image:image_id(id, image_name, image_url, alt_text),
                    user:user_id(id, username, email)
                ''').eq('id', created_product['id']).execute()
                
                return Response({
                    'message': 'Product created successfully with image',
                    'product': complete_product.data[0] if complete_product.data else created_product,
                    'workflow': {
                        'step_1': 'Image uploaded to Cloudinary',
                        'step_2': f'Image metadata saved with ID: {image_id}',
                        'step_3': f'Product created with image_id: {image_id}'
                    }
                }, status=status.HTTP_201_CREATED)
            else:
                # If product creation fails, clean up the uploaded image
                try:
                    supabase.table('images').delete().eq('id', image_id).execute()
                except:
                    pass  # Ignore cleanup errors
                    
                return Response({
                    'error': 'Failed to create product'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            # If product creation fails, clean up the uploaded image
            try:
                supabase.table('images').delete().eq('id', image_id).execute()
            except:
                pass  # Ignore cleanup errors
                
            return Response({
                'error': f'Failed to create product: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    except Exception as e:
        return Response({
            'error': f'An error occurred: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)