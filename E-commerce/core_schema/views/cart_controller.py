from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from supabase import create_client, Client
from decouple import config
from ..serializers.cart_serializer import CartSerializer

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
@permission_classes([IsAuthenticated])
def cart_list(request):
    """
    List user's cart items
    """
    try:
        user_id = get_user_id_from_token(request)
        if not user_id:
            return Response({
                'error': 'Invalid or missing authentication token'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        result = supabase.table('cart').select('''
            *,
            product:product_id(id, name, price, image_id, stock),
            user:user_id(id, username, email)
        ''').eq('user_id', user_id).execute()
        
        # Calculate total
        total = 0
        for item in result.data:
            if item.get('product'):
                total += float(item.get('product', {}).get('price', 0)) * int(item.get('quantity', 0))
        
        return Response({
            'cart_items': result.data,
            'total': total,
            'count': len(result.data)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': f'An error occurred while fetching cart: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def cart_detail(request, cart_id):
    """
    Get details of a specific cart item
    """
    try:
        user_id = get_user_id_from_token(request)
        if not user_id:
            return Response({
                'error': 'Invalid or missing authentication token'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        result = supabase.table('cart').select('''
            *,
            product:product_id(id, name, price, image_id, stock),
            user:user_id(id, username, email)
        ''').eq('id', cart_id).eq('user_id', user_id).execute()
        
        if not result.data:
            return Response({
                'error': 'Cart item not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        cart_item = result.data[0]
        
        return Response({
            'cart_item': cart_item
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': f'An error occurred while fetching cart item: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CartController(APIView):
    """
    Cart Controller using Supabase for CRUD operations
    """
    
    @permission_classes([IsAuthenticated])
    def get(self, request):
        """
        List user's cart items
        """
        return cart_list(request)
    
    @permission_classes([IsAuthenticated])
    def post(self, request):
        """
        Add item to cart
        """
        try:
            user_id = get_user_id_from_token(request)
            if not user_id:
                return Response({
                    'error': 'Invalid or missing authentication token'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            data = request.data
            
            required_fields = ['product_id', 'quantity']
            if not all(field in data for field in required_fields):
                return Response({
                    'error': f'Required fields: {", ".join(required_fields)}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            product_id = int(data['product_id'])
            quantity = int(data['quantity'])
            
            if quantity <= 0:
                return Response({
                    'error': 'Quantity must be greater than 0'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if product exists and has sufficient stock
            product_result = supabase.table('product').select('*').eq('id', product_id).execute()
            if not product_result.data:
                return Response({
                    'error': 'Product not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            product = product_result.data[0]
            if product.get('stock', 0) < quantity:
                return Response({
                    'error': 'Insufficient stock'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if item already exists in cart
            existing_cart = supabase.table('cart').select('*').eq('user_id', user_id).eq('product_id', product_id).execute()
            
            if existing_cart.data:
                # Update quantity
                existing_item = existing_cart.data[0]
                new_quantity = existing_item.get('quantity', 0) + quantity
                
                if product.get('stock', 0) < new_quantity:
                    return Response({
                        'error': 'Insufficient stock for updated quantity'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                result = supabase.table('cart').update({
                    'quantity': new_quantity
                }).eq('id', existing_item['id']).execute()
                
                return Response({
                    'message': 'Cart item quantity updated',
                    'cart_item': result.data[0] if result.data else None
                }, status=status.HTTP_200_OK)
            else:
                # Add new item
                cart_data = {
                    'user_id': user_id,
                    'product_id': product_id,
                    'quantity': quantity
                }
                
                result = supabase.table('cart').insert(cart_data).execute()
                
                if result.data:
                    return Response({
                        'message': 'Item added to cart successfully',
                        'cart_item': result.data[0]
                    }, status=status.HTTP_201_CREATED)
                else:
                    return Response({
                        'error': 'Failed to add item to cart'
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except ValueError as e:
            return Response({
                'error': f'Invalid data format: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'error': f'An error occurred while adding to cart: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def list_cart(self, request):
        return self.get(request)
        
    def get_cart(self, request, cart_id):
        return cart_detail(request, cart_id)
        
    def add_to_cart(self, request):
        return self.post(request)
        
    def update_cart(self, request, cart_id):
        """
        Update cart item quantity
        """
        try:
            user_id = get_user_id_from_token(request)
            if not user_id:
                return Response({
                    'error': 'Invalid or missing authentication token'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            data = request.data
            
            # Check if cart item exists and belongs to user
            existing_cart = supabase.table('cart').select('*').eq('id', cart_id).eq('user_id', user_id).execute()
            if not existing_cart.data:
                return Response({
                    'error': 'Cart item not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            cart_item = existing_cart.data[0]
            
            if 'quantity' in data:
                quantity = int(data['quantity'])
                
                if quantity <= 0:
                    return Response({
                        'error': 'Quantity must be greater than 0'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Check product stock
                product_result = supabase.table('product').select('*').eq('id', cart_item['product_id']).execute()
                if product_result.data:
                    product = product_result.data[0]
                    if product.get('stock', 0) < quantity:
                        return Response({
                            'error': 'Insufficient stock'
                        }, status=status.HTTP_400_BAD_REQUEST)
                
                result = supabase.table('cart').update({
                    'quantity': quantity
                }).eq('id', cart_id).execute()
                
                if result.data:
                    return Response({
                        'message': 'Cart item updated successfully',
                        'cart_item': result.data[0]
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
                'error': f'An error occurred while updating cart: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def remove_from_cart(self, request, cart_id):
        """
        Remove item from cart
        """
        try:
            user_id = get_user_id_from_token(request)
            if not user_id:
                return Response({
                    'error': 'Invalid or missing authentication token'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            # Check if cart item exists and belongs to user
            existing_cart = supabase.table('cart').select('*').eq('id', cart_id).eq('user_id', user_id).execute()
            if not existing_cart.data:
                return Response({
                    'error': 'Cart item not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            result = supabase.table('cart').delete().eq('id', cart_id).execute()
            
            return Response({
                'message': 'Item removed from cart successfully'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': f'An error occurred while removing from cart: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def clear_cart(self, request):
        """
        Clear all items from user's cart
        """
        try:
            user_id = get_user_id_from_token(request)
            if not user_id:
                return Response({
                    'error': 'Invalid or missing authentication token'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            result = supabase.table('cart').delete().eq('user_id', user_id).execute()
            
            return Response({
                'message': 'Cart cleared successfully'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': f'An error occurred while clearing cart: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
