from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from supabase import create_client, Client
from decouple import config
from ..serializers.review_serializer import ReviewSerializer

# Initialize Supabase client
SUPABASE_URL = str(config('Database_Url'))
SUPABASE_KEY = str(config('Database_key'))

# Ensure environment variables are loaded
if not SUPABASE_URL or not SUPABASE_KEY or SUPABASE_URL == 'None' or SUPABASE_KEY == 'None':
    raise ValueError("Missing Supabase configuration. Please check your .env file.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_user_id_from_token(request):
    """
    Extract user ID from JWT token
    """
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return None
        
        token = auth_header.split(' ')[1]
        jwt_auth = JWTAuthentication()
        validated_token = jwt_auth.get_validated_token(token)
        return validated_token.get('user_id')
    except (InvalidToken, TokenError):
        return None

@api_view(['GET'])
@permission_classes([AllowAny])
def review_list(request):
    """
    List reviews with pagination and filtering
    """
    try:
        page = int(request.GET.get('page', 1))
        limit = int(request.GET.get('limit', 10))
        product_id = request.GET.get('product_id')
        rating_filter = request.GET.get('rating')
        
        offset = (page - 1) * limit
        
        query = supabase.table('review').select('''
            *,
            product:product_id(id, name),
            user:user_id(id, username)
        ''')
        
        if product_id:
            query = query.eq('product_id', product_id)
        
        if rating_filter:
            query = query.eq('rating', int(rating_filter))
        
        result = query.order('created_at', desc=True).range(offset, offset + limit - 1).execute()
        
        # Get total count
        count_query = supabase.table('review').select('*')
        if product_id:
            count_query = count_query.eq('product_id', product_id)
        if rating_filter:
            count_query = count_query.eq('rating', int(rating_filter))
            
        count_result = count_query.execute()
        total_count = len(count_result.data) if count_result.data else 0
        
        return Response({
            'reviews': result.data,
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
            'error': f'An error occurred while fetching reviews: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def review_detail(request, review_id):
    """
    Get details of a specific review
    """
    try:
        result = supabase.table('review').select('''
            *,
            product:product_id(id, name, price),
            user:user_id(id, username, first_name, last_name)
        ''').eq('id', review_id).execute()
        
        if not result.data:
            return Response({
                'error': 'Review not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        review = result.data[0]
        
        return Response({
            'review': review
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': f'An error occurred while fetching review: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ReviewController(APIView):
    """
    Review Controller using Supabase for CRUD operations
    """
    
    @permission_classes([AllowAny])
    def get(self, request):
        """
        List reviews
        """
        return review_list(request)
    
    @permission_classes([IsAuthenticated])
    def post(self, request):
        """
        Add a new review
        """
        try:
            user_id = get_user_id_from_token(request)
            if not user_id:
                return Response({
                    'error': 'Invalid or missing authentication token'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            data = request.data
            
            required_fields = ['product_id', 'rating']
            if not all(field in data for field in required_fields):
                return Response({
                    'error': f'Required fields: {", ".join(required_fields)}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            product_id = int(data['product_id'])
            rating = int(data['rating'])
            
            # Validate rating
            if rating < 1 or rating > 5:
                return Response({
                    'error': 'Rating must be between 1 and 5'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if product exists
            product_result = supabase.table('product').select('*').eq('id', product_id).execute()
            if not product_result.data:
                return Response({
                    'error': 'Product not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Check if user has already reviewed this product
            existing_review = supabase.table('review').select('*').eq('user_id', user_id).eq('product_id', product_id).execute()
            if existing_review.data:
                return Response({
                    'error': 'You have already reviewed this product'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if user has purchased this product
            order_check = supabase.table('order_items').select('''
                *,
                order:order_id!inner(user_id, status)
            ''').eq('product_id', product_id).execute()
            
            user_has_purchased = False
            for item in order_check.data:
                order = item.get('order', {})
                if order.get('user_id') == user_id and order.get('status') in ['delivered', 'completed']:
                    user_has_purchased = True
                    break
            
            if not user_has_purchased:
                return Response({
                    'error': 'You can only review products you have purchased'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            review_data = {
                'user_id': user_id,
                'product_id': product_id,
                'rating': rating,
                'comment': data.get('comment', '')
            }
            
            result = supabase.table('review').insert(review_data).execute()
            
            if result.data:
                review = result.data[0]
                return Response({
                    'message': 'Review added successfully',
                    'review': review
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    'error': 'Failed to add review'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except ValueError as e:
            return Response({
                'error': f'Invalid data format: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'error': f'An error occurred while adding review: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def list_reviews(self, request):
        return self.get(request)
        
    def get_review(self, request, review_id):
        return review_detail(request, review_id)
        
    def add_review(self, request):
        return self.post(request)
        
    def update_review(self, request, review_id):
        """
        Update a review (only by the author)
        """
        try:
            user_id = get_user_id_from_token(request)
            if not user_id:
                return Response({
                    'error': 'Invalid or missing authentication token'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            data = request.data
            
            # Check if review exists and belongs to user
            existing_review = supabase.table('review').select('*').eq('id', review_id).eq('user_id', user_id).execute()
            if not existing_review.data:
                return Response({
                    'error': 'Review not found or you are not authorized to update it'
                }, status=status.HTTP_404_NOT_FOUND)
            
            update_data = {}
            updatable_fields = ['rating', 'comment']
            
            for field in updatable_fields:
                if field in data:
                    if field == 'rating':
                        rating = int(data[field])
                        if rating < 1 or rating > 5:
                            return Response({
                                'error': 'Rating must be between 1 and 5'
                            }, status=status.HTTP_400_BAD_REQUEST)
                        update_data[field] = rating
                    else:
                        update_data[field] = data[field]
            
            if update_data:
                result = supabase.table('review').update(update_data).eq('id', review_id).execute()
                
                if result.data:
                    return Response({
                        'message': 'Review updated successfully',
                        'review': result.data[0]
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
                'error': f'An error occurred while updating review: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def delete_review(self, request, review_id):
        """
        Delete a review (only by the author)
        """
        try:
            user_id = get_user_id_from_token(request)
            if not user_id:
                return Response({
                    'error': 'Invalid or missing authentication token'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            # Check if review exists and belongs to user
            existing_review = supabase.table('review').select('*').eq('id', review_id).eq('user_id', user_id).execute()
            if not existing_review.data:
                return Response({
                    'error': 'Review not found or you are not authorized to delete it'
                }, status=status.HTTP_404_NOT_FOUND)
            
            result = supabase.table('review').delete().eq('id', review_id).execute()
            
            return Response({
                'message': 'Review deleted successfully'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': f'An error occurred while deleting review: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
