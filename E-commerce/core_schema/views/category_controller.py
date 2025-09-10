
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from supabase import create_client, Client
from decouple import config
from ..serializers.category_serializer import CategorySerializer

# Initialize Supabase client
SUPABASE_URL = str(config('Database_Url'))
SUPABASE_KEY = str(config('Database_key'))

# Ensure environment variables are loaded
if not SUPABASE_URL or not SUPABASE_KEY or SUPABASE_URL == 'None' or SUPABASE_KEY == 'None':
    raise ValueError("Missing Supabase configuration. Please check your .env file.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@api_view(['GET'])
@permission_classes([AllowAny])
def category_list(request):
    """
    List all categories with pagination
    """
    try:
        page = int(request.GET.get('page', 1))
        limit = int(request.GET.get('limit', 10))
        search = request.GET.get('search')
        
        offset = (page - 1) * limit
        
        query = supabase.table('category').select('*')
        
        if search:
            query = query.ilike('name', f'%{search}%')
        
        result = query.order('created_at', desc=True).range(offset, offset + limit - 1).execute()
        
        # Get total count
        count_result = supabase.table('category').select('*').execute()
        total_count = len(count_result.data) if count_result.data else 0
        
        return Response({
            'categories': result.data,
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
            'error': f'An error occurred while fetching categories: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def category_detail(request, category_id):
    """
    Get details of a specific category
    """
    try:
        result = supabase.table('category').select('*').eq('id', category_id).execute()
        
        if not result.data:
            return Response({
                'error': 'Category not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        category = result.data[0]
        
        return Response({
            'category': category
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': f'An error occurred while fetching category: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CategoryController(APIView):
    """
    Category Controller using Supabase for CRUD operations
    """
    
    @permission_classes([AllowAny])
    def get(self, request):
        """
        List all categories
        """
        return category_list(request)
    
    @permission_classes([IsAuthenticated])
    def post(self, request):
        """
        Create a new category
        """
        try:
            data = request.data
            
            required_fields = ['name']
            if not all(field in data for field in required_fields):
                return Response({
                    'error': f'Required fields: {", ".join(required_fields)}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if category name already exists
            existing_category = supabase.table('category').select('id').eq('name', data['name']).execute()
            if existing_category.data:
                return Response({
                    'error': 'Category name already exists'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            category_data = {
                'name': data['name'],
                'description': data.get('description', '')
            }
            
            result = supabase.table('category').insert(category_data).execute()
            
            if result.data:
                category = result.data[0]
                return Response({
                    'message': 'Category created successfully',
                    'category': category
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    'error': 'Failed to create category'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            return Response({
                'error': f'An error occurred while creating category: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def list_categories(self, request):
        return self.get(request)
        
    def get_category(self, request, category_id):
        return category_detail(request, category_id)
        
    def create_category(self, request):
        return self.post(request)
        
    def update_category(self, request, category_id):
        """
        Update an existing category
        """
        try:
            data = request.data
            
            existing_category = supabase.table('category').select('*').eq('id', category_id).execute()
            if not existing_category.data:
                return Response({
                    'error': 'Category not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            update_data = {}
            updatable_fields = ['name', 'description']
            
            for field in updatable_fields:
                if field in data:
                    update_data[field] = data[field]
            
            if 'name' in update_data:
                current_category = existing_category.data[0]
                if update_data['name'] != current_category.get('name'):
                    name_check = supabase.table('category').select('id').eq('name', update_data['name']).neq('id', category_id).execute()
                    if name_check.data:
                        return Response({
                            'error': 'Category name already exists'
                        }, status=status.HTTP_400_BAD_REQUEST)
            
            if update_data:
                result = supabase.table('category').update(update_data).eq('id', category_id).execute()
                
                if result.data:
                    updated_category = result.data[0]
                    return Response({
                        'message': 'Category updated successfully',
                        'category': updated_category
                    }, status=status.HTTP_200_OK)
            
            return Response({
                'message': 'No changes made'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': f'An error occurred while updating category: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def delete_category(self, request, category_id):
        """
        Delete a category
        """
        try:
            existing_category = supabase.table('category').select('*').eq('id', category_id).execute()
            if not existing_category.data:
                return Response({
                    'error': 'Category not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Check if category has products
            products_check = supabase.table('product').select('id').eq('category_id', category_id).execute()
            if products_check.data:
                return Response({
                    'error': 'Cannot delete category with existing products'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            result = supabase.table('category').delete().eq('id', category_id).execute()
            
            return Response({
                'message': 'Category deleted successfully'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': f'An error occurred while deleting category: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)