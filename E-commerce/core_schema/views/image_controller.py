import cloudinary
import cloudinary.api
from django.http import HttpRequest, HttpResponse
from cloudinary.utils import cloudinary_url
from cloudinary.uploader import upload
import cloudinary.uploader
from decouple import config
from rest_framework.viewsets import ModelViewSet
from rest_framework import serializers, status
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from supabase import create_client, Client
from ..models.Images import Images
from ..serializers.image_serializer import ImageSerializer

CLOUDINARY_CLOUD_NAME = str(config('CLOUDINARY_CLOUD_NAME'))
CLOUDINARY_URL = str(config('CLOUDINARY_URL'))
CLOUDINARY_KEY = str(config('CLOUDINARY_API_KEY'))
CLOUDINARY_SECRET = str(config('CLOUDINARY_API_SECRET'))

# Initialize Supabase client
SUPABASE_URL = str(config('Database_Url'))
SUPABASE_KEY = str(config('Database_key'))

# Ensure environment variables are loaded
if not SUPABASE_URL or not SUPABASE_KEY or SUPABASE_URL == 'None' or SUPABASE_KEY == 'None':
    raise ValueError("Missing Supabase configuration. Please check your .env file.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Configure Cloudinary
cloudinary.config( 
    cloud_name=CLOUDINARY_CLOUD_NAME, 
    api_key=CLOUDINARY_KEY, 
    api_secret=CLOUDINARY_SECRET,
    secure=True
)


def image_list(request):
    pass

def image_detail(request, image_id):
    pass

def cloudinary_upload_helper(image_file):
    """
    Helper to upload image to Cloudinary using the exact same logic as simple_cloudinary_test
    """
    if hasattr(image_file, 'seek'):
        image_file.seek(0)
    return cloudinary.uploader.upload(
        image_file,
        folder="test_uploads",
        resource_type="auto"
    )

@api_view(['POST'])
@permission_classes([AllowAny])  # Temporarily disable auth to test
def upload_image(request):
    """
    Upload image to Cloudinary and save metadata to Supabase database
    """
    try:
        print("=== DEBUG INFO ===")
        print(f"Request method: {request.method}")
        print(f"Request FILES: {request.FILES}")
        print(f"Request data: {request.data}")
        print(f"Content type: {request.content_type}")
        
        # Check if image file is provided
        if 'image' not in request.FILES:
            print("No image file provided in request")
            print("Available FILES keys:", list(request.FILES.keys()))
            return Response({
                'error': 'No image file provided',
                'available_keys': list(request.FILES.keys()),
                'request_data': dict(request.data)
            }, status=status.HTTP_400_BAD_REQUEST)
        
        image_file = request.FILES['image']
        
        image_file = request.FILES['image']
        
        print(f"Image file info:")
        print(f"  - Name: {image_file.name}")
        print(f"  - Size: {image_file.size}")
        print(f"  - Content type: {image_file.content_type}")
        
        # Get optional fields
        image_name = request.data.get('image_name', image_file.name)
        alt_text = request.data.get('alt_text', '')
        
        print(f"Processing image: {image_name}")
        print(f"Cloudinary config check:")
        print(f"Cloud name: {CLOUDINARY_CLOUD_NAME}")
        print(f"API Key: {CLOUDINARY_KEY[:4]}***" if CLOUDINARY_KEY else "Not set")
        print(f"API Secret: {'*' * len(CLOUDINARY_SECRET)}" if CLOUDINARY_SECRET else "Not set")
        
        # Validate image file
        if not image_file.content_type.startswith('image/'):
            return Response({
                'error': 'File must be an image'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check file size (limit to 10MB)
        if image_file.size > 10 * 1024 * 1024:
            return Response({
                'error': 'Image file too large. Maximum size is 10MB'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if image_name already exists in Supabase
        existing_image = supabase.table('images').select('id').eq('image_name', image_name).execute()
        if existing_image.data:
            return Response({
                'error': 'Image name already exists'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Upload to Cloudinary using helper function
        try:
            print(f"Uploading to Cloudinary with image: {image_name}")
            upload_result = cloudinary_upload_helper(image_file)
            print(f"Cloudinary upload result: {upload_result}")
            
        except Exception as cloudinary_error:
            print(f"Cloudinary upload error: {str(cloudinary_error)}")
            return Response({
                'error': f'Cloudinary upload failed: {str(cloudinary_error)}',
                'debug_info': {
                    'cloud_name': CLOUDINARY_CLOUD_NAME,
                    'api_key_length': len(CLOUDINARY_KEY) if CLOUDINARY_KEY else 0,
                    'api_secret_length': len(CLOUDINARY_SECRET) if CLOUDINARY_SECRET else 0
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Extract the public accessible URL from Cloudinary response
        cloudinary_public_url = upload_result.get('secure_url')
        public_id = upload_result.get('public_id')
        
        if not cloudinary_public_url:
            return Response({
                'error': 'Failed to upload image to Cloudinary'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Prepare data for Supabase
        image_data = {
            'image_name': image_name,
            'image_url': cloudinary_public_url,  # Save the public accessible URL
            'alt_text': alt_text
        }
        
        # Save to Supabase
        result = supabase.table('images').insert(image_data).execute()
        
        if result.data:
            saved_image = result.data[0]
            return Response({
                'message': 'Image uploaded successfully',
                'image': {
                    'id': saved_image.get('id'),
                    'image_name': saved_image.get('image_name'),
                    'image_url': saved_image.get('image_url'),  # This is the public accessible URL
                    'alt_text': saved_image.get('alt_text'),
                    'cloudinary_public_id': public_id,
                    'created_at': saved_image.get('created_at'),
                    'updated_at': saved_image.get('updated_at')
                }
            }, status=status.HTTP_201_CREATED)
        else:
            # If database save fails, delete from Cloudinary
            cloudinary.uploader.destroy(public_id)
            return Response({
                'error': 'Failed to save image metadata to database'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        return Response({
            'error': f'An error occurred while uploading image: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ImageController():

    """
    Controller for handling image operations
    """
    queryset = Images.objects.all()
    serializer_class = ImageSerializer



    def list_images(self, request):
        pass
    def get_image(self, request, image_id):
        pass

    def upload_image(self, request):
        """
        Upload image to Cloudinary and save metadata to Supabase database
        """
        try:
            # Check if image file is provided
            if 'image' not in request.FILES:
                return Response({
                    'error': 'No image file provided'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            image_file = request.FILES['image']
            
            # Get optional fields
            image_name = request.data.get('image_name', image_file.name)
            alt_text = request.data.get('alt_text', '')
            
            # Validate image file
            if not image_file.content_type.startswith('image/'):
                return Response({
                    'error': 'File must be an image'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check file size (limit to 10MB)
            if image_file.size > 10 * 1024 * 1024:
                return Response({
                    'error': 'Image file too large. Maximum size is 10MB'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if image_name already exists in Supabase
            existing_image = supabase.table('images').select('id').eq('image_name', image_name).execute()
            if existing_image.data:
                return Response({
                    'error': 'Image name already exists'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Upload to Cloudinary
            upload_result = cloudinary.uploader.upload(
                image_file,
                folder="ecommerce/products",  # Organize in folders
                public_id=image_name.split('.')[0],  # Use image name as public_id
                overwrite=True,
                resource_type="image",
                format="auto",  # Auto-optimize format
                quality="auto",  # Auto-optimize quality
                fetch_format="auto"
            )
            
            # Extract the public accessible URL from Cloudinary response
            cloudinary_public_url = upload_result.get('secure_url')
            public_id = upload_result.get('public_id')
            
            if not cloudinary_public_url:
                return Response({
                    'error': 'Failed to upload image to Cloudinary'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Prepare data for Supabase
            image_data = {
                'image_name': image_name,
                'image_url': cloudinary_public_url,  # Save the public accessible URL
                'alt_text': alt_text
            }
            
            # Save to Supabase
            result = supabase.table('images').insert(image_data).execute()
            
            if result.data:
                saved_image = result.data[0]
                return Response({
                    'message': 'Image uploaded successfully',
                    'image': {
                        'id': saved_image.get('id'),
                        'image_name': saved_image.get('image_name'),
                        'image_url': saved_image.get('image_url'),  # This is the public accessible URL
                        'alt_text': saved_image.get('alt_text'),
                        'cloudinary_public_id': public_id,
                        'created_at': saved_image.get('created_at'),
                        'updated_at': saved_image.get('updated_at')
                    }
                }, status=status.HTTP_201_CREATED)
            else:
                # If database save fails, delete from Cloudinary
                cloudinary.uploader.destroy(public_id)
                return Response({
                    'error': 'Failed to save image metadata to database'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            return Response({
                'error': f'An error occurred while uploading image: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ImageUploadAPIView(APIView):
    """
    Alternative class-based view for image upload
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            if 'image' not in request.FILES:
                return Response({
                    'error': 'No image file provided'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            image_file = request.FILES['image']
            
            # Simple upload
            upload_result = cloudinary.uploader.upload(
                image_file,
                folder="ecommerce/class_based",
                resource_type="auto"
            )
            
            return Response({
                'message': 'Class-based upload successful',
                'url': upload_result.get('secure_url')
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def upload_image_test(request):
    """
    Test image upload without authentication (for debugging)
    """
    try:
        # Check if image file is provided
        if 'image' not in request.FILES:
            return Response({
                'error': 'No image file provided'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        image_file = request.FILES['image']
        
        # Get optional fields
        image_name = request.data.get('image_name', image_file.name)
        alt_text = request.data.get('alt_text', '')
        
        # Validate image file
        if not image_file.content_type.startswith('image/'):
            return Response({
                'error': 'File must be an image'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check file size (limit to 10MB)
        if image_file.size > 10 * 1024 * 1024:
            return Response({
                'error': 'Image file too large. Maximum size is 10MB'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Upload to Cloudinary
        upload_result = cloudinary.uploader.upload(
            image_file,
            folder="ecommerce/products/test",  # Test folder
            public_id=image_name.split('.')[0],
            overwrite=True,
            resource_type="image"
        )
        
        # Extract the public accessible URL
        cloudinary_public_url = upload_result.get('secure_url')
        public_id = upload_result.get('public_id')
        
        if not cloudinary_public_url:
            return Response({
                'error': 'Failed to upload image to Cloudinary'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            'message': 'Image uploaded successfully (test mode)',
            'image_url': cloudinary_public_url,
            'public_id': public_id,
            'note': 'This is a test endpoint without authentication'
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'error': f'An error occurred while uploading image: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def test_cloudinary_config(request):
    """
    Test Cloudinary configuration
    """
    try:
        # Show exactly what's being loaded
        print("=== CLOUDINARY CONFIG DEBUG ===")
        print(f"Raw CLOUDINARY_CLOUD_NAME: '{CLOUDINARY_CLOUD_NAME}'")
        print(f"Raw CLOUDINARY_KEY: '{CLOUDINARY_KEY}'")
        print(f"Raw CLOUDINARY_SECRET: '{CLOUDINARY_SECRET}'")
        print(f"Raw CLOUDINARY_URL: '{CLOUDINARY_URL}'")
        
        # Test different configuration approaches
        
        # Method 1: Direct configuration
        cloudinary.config( 
            cloud_name=CLOUDINARY_CLOUD_NAME.strip(), 
            api_key=CLOUDINARY_KEY.strip(), 
            api_secret=CLOUDINARY_SECRET.strip(),
            secure=True
        )
        
        # Try a simple operation that doesn't require authentication
        test_result = cloudinary.api.ping()
        
        return Response({
            'message': 'Cloudinary configuration is working',
            'config': {
                'cloud_name': CLOUDINARY_CLOUD_NAME.strip(),
                'api_key': CLOUDINARY_KEY.strip()[:4] + '***' if CLOUDINARY_KEY else 'Not set',
                'api_secret': CLOUDINARY_SECRET.strip()[:4] + '***' if CLOUDINARY_SECRET else 'Not set'
            },
            'ping_result': test_result,
            'method': 'Direct config'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        # Try method 2: Using CLOUDINARY_URL
        try:
            import os
            os.environ['CLOUDINARY_URL'] = CLOUDINARY_URL
            
            # Reconfigure
            cloudinary.config()
            
            test_result = cloudinary.api.ping()
            
            return Response({
                'message': 'Cloudinary configuration working with URL method',
                'config': {
                    'cloudinary_url': CLOUDINARY_URL[:50] + '...' if len(CLOUDINARY_URL) > 50 else CLOUDINARY_URL
                },
                'ping_result': test_result,
                'method': 'URL config'
            }, status=status.HTTP_200_OK)
            
        except Exception as url_error:
            return Response({
                'error': f'Both config methods failed',
                'direct_config_error': str(e),
                'url_config_error': str(url_error),
                'config_check': {
                    'cloud_name': CLOUDINARY_CLOUD_NAME.strip() if CLOUDINARY_CLOUD_NAME else 'Not set',
                    'api_key': 'Set' if CLOUDINARY_KEY else 'Not set',
                    'api_secret': 'Set' if CLOUDINARY_SECRET else 'Not set',
                    'cloudinary_url': 'Set' if CLOUDINARY_URL else 'Not set'
                },
                'raw_values': {
                    'cloud_name_length': len(CLOUDINARY_CLOUD_NAME) if CLOUDINARY_CLOUD_NAME else 0,
                    'api_key_length': len(CLOUDINARY_KEY) if CLOUDINARY_KEY else 0,
                    'api_secret_length': len(CLOUDINARY_SECRET) if CLOUDINARY_SECRET else 0
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def debug_file_upload(request):
    """
    Debug endpoint to test file upload without any processing
    """
    try:
        print("=== FILE UPLOAD DEBUG ===")
        print(f"Request method: {request.method}")
        print(f"Content type: {request.content_type}")
        print(f"Request FILES: {dict(request.FILES)}")
        print(f"Request POST: {dict(request.POST)}")
        print(f"Request data: {dict(request.data)}")
        
        response_data = {
            'message': 'Debug info collected',
            'request_info': {
                'method': request.method,
                'content_type': request.content_type,
                'has_files': bool(request.FILES),
                'files_count': len(request.FILES),
                'file_keys': list(request.FILES.keys()),
                'post_data': dict(request.POST),
                'data_keys': list(request.data.keys())
            }
        }
        
        if request.FILES:
            for key, file_obj in request.FILES.items():
                response_data[f'file_{key}'] = {
                    'name': file_obj.name,
                    'size': file_obj.size,
                    'content_type': file_obj.content_type,
                    'charset': getattr(file_obj, 'charset', None)
                }
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': f'Debug error: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def simple_cloudinary_test(request):
    """
    Simple test to upload to Cloudinary without Supabase
    """
    try:
        if 'image' not in request.FILES:
            return Response({
                'error': 'No image file provided'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        image_file = request.FILES['image']
        
        # Use shared helper for upload
        upload_result = cloudinary_upload_helper(image_file)
        
        return Response({
            'message': 'Upload successful',
            'cloudinary_url': upload_result.get('secure_url'),
            'public_id': upload_result.get('public_id'),
            'format': upload_result.get('format'),
            'bytes': upload_result.get('bytes')
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'error': f'Upload failed: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete_image(self, request, image_id):
        pass

    def upload_image(self, request):
        """
        Upload image to Cloudinary and save metadata to Supabase database
        """
        try:
            # Check if image file is provided
            if 'image' not in request.FILES:
                return Response({
                    'error': 'No image file provided'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            image_file = request.FILES['image']
            
            # Get optional fields
            image_name = request.data.get('image_name', image_file.name)
            alt_text = request.data.get('alt_text', '')
            
            # Validate image file
            if not image_file.content_type.startswith('image/'):
                return Response({
                    'error': 'File must be an image'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check file size (limit to 10MB)
            if image_file.size > 10 * 1024 * 1024:
                return Response({
                    'error': 'Image file too large. Maximum size is 10MB'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Upload to Cloudinary using shared helper
            upload_result = cloudinary_upload_helper(image_file)
            return Response({
                'message': 'Upload successful',
                'cloudinary_url': upload_result.get('secure_url'),
                'public_id': upload_result.get('public_id'),
                'format': upload_result.get('format'),
                'bytes': upload_result.get('bytes')
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'error': f'An error occurred while uploading image: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    def delete_image(self, request, image_id):
        pass
