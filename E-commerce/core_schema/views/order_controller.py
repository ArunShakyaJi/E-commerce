from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from supabase import create_client, Client
from decouple import config
from datetime import datetime
from ..serializers.order_serializer import OrderSerializer
from ..serializers.order_items_serializer import OrderItemSerializer

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
def order_list(request):
    """
    List user's orders
    """
    try:
        user_id = get_user_id_from_token(request)
        if not user_id:
            return Response({
                'error': 'Invalid or missing authentication token'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        page = int(request.GET.get('page', 1))
        limit = int(request.GET.get('limit', 10))
        status_filter = request.GET.get('status')
        
        offset = (page - 1) * limit
        
        query = supabase.table('orders').select('''
            *,
            user:user_id(id, username, email)
        ''').eq('user_id', user_id)
        
        if status_filter:
            query = query.eq('status', status_filter)
        
        result = query.order('created_at', desc=True).range(offset, offset + limit - 1).execute()
        
        # Get total count
        count_result = supabase.table('orders').select('*').eq('user_id', user_id).execute()
        total_count = len(count_result.data) if count_result.data else 0
        
        return Response({
            'orders': result.data,
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
            'error': f'An error occurred while fetching orders: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def order_detail(request, order_id):
    """
    Get details of a specific order
    """
    try:
        user_id = get_user_id_from_token(request)
        if not user_id:
            return Response({
                'error': 'Invalid or missing authentication token'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Get order details
        order_result = supabase.table('orders').select('''
            *,
            user:user_id(id, username, email, first_name, last_name)
        ''').eq('id', order_id).eq('user_id', user_id).execute()
        
        if not order_result.data:
            return Response({
                'error': 'Order not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        order = order_result.data[0]
        
        # Get order items
        items_result = supabase.table('order_items').select('''
            *,
            product:product_id(id, name, price, image_id)
        ''').eq('order_id', order_id).execute()
        
        order['items'] = items_result.data
        
        return Response({
            'order': order
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': f'An error occurred while fetching order: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class OrderController(APIView):
    """
    Order Controller using Supabase for CRUD operations
    """
    
    @permission_classes([IsAuthenticated])
    def get(self, request):
        """
        List user's orders
        """
        return order_list(request)
    
    @permission_classes([IsAuthenticated])
    def post(self, request):
        """
        Place a new order from cart items
        """
        try:
            user_id = get_user_id_from_token(request)
            if not user_id:
                return Response({
                    'error': 'Invalid or missing authentication token'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            data = request.data
            
            # Get user's cart items
            cart_result = supabase.table('cart').select('''
                *,
                product:product_id(id, name, price, stock)
            ''').eq('user_id', user_id).execute()
            
            if not cart_result.data:
                return Response({
                    'error': 'Cart is empty'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Calculate total and validate stock
            total_amount = 0
            order_items = []
            
            for cart_item in cart_result.data:
                product = cart_item.get('product', {})
                quantity = cart_item.get('quantity', 0)
                price = float(product.get('price', 0))
                
                # Check stock availability
                if product.get('stock', 0) < quantity:
                    return Response({
                        'error': f'Insufficient stock for product: {product.get("name", "Unknown")}'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                item_total = price * quantity
                total_amount += item_total
                
                order_items.append({
                    'product_id': product.get('id'),
                    'quantity': quantity,
                    'price': price,
                    'total': item_total
                })
            
            # Create order
            order_data = {
                'user_id': user_id,
                'total_amount': total_amount,
                'status': 'pending',
                'shipping_address': data.get('shipping_address', ''),
                'payment_method': data.get('payment_method', 'cash_on_delivery')
            }
            
            order_result = supabase.table('orders').insert(order_data).execute()
            
            if not order_result.data:
                return Response({
                    'error': 'Failed to create order'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            order = order_result.data[0]
            order_id = order['id']
            
            # Create order items
            for item in order_items:
                item['order_id'] = order_id
            
            items_result = supabase.table('order_items').insert(order_items).execute()
            
            if not items_result.data:
                # Rollback order creation
                supabase.table('orders').delete().eq('id', order_id).execute()
                return Response({
                    'error': 'Failed to create order items'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Update product stock
            for cart_item in cart_result.data:
                product = cart_item.get('product', {})
                quantity = cart_item.get('quantity', 0)
                new_stock = product.get('stock', 0) - quantity
                
                supabase.table('product').update({
                    'stock': new_stock
                }).eq('id', product.get('id')).execute()
            
            # Clear user's cart
            supabase.table('cart').delete().eq('user_id', user_id).execute()
            
            return Response({
                'message': 'Order placed successfully',
                'order': {
                    'id': order_id,
                    'total_amount': total_amount,
                    'status': 'pending',
                    'items': items_result.data
                }
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'error': f'An error occurred while placing order: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def list_orders(self, request):
        return self.get(request)
        
    def get_order(self, request, order_id):
        return order_detail(request, order_id)
        
    def place_order(self, request):
        return self.post(request)
        
    def update_order(self, request, order_id):
        """
        Update order status (admin only for now)
        """
        try:
            user_id = get_user_id_from_token(request)
            if not user_id:
                return Response({
                    'error': 'Invalid or missing authentication token'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            data = request.data
            
            # Check if order exists and belongs to user
            existing_order = supabase.table('orders').select('*').eq('id', order_id).eq('user_id', user_id).execute()
            if not existing_order.data:
                return Response({
                    'error': 'Order not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            order = existing_order.data[0]
            
            # Only allow certain status updates
            allowed_updates = ['shipping_address']
            if order.get('status') == 'pending':
                allowed_updates.append('payment_method')
            
            update_data = {}
            for field in allowed_updates:
                if field in data:
                    update_data[field] = data[field]
            
            if update_data:
                result = supabase.table('orders').update(update_data).eq('id', order_id).execute()
                
                if result.data:
                    return Response({
                        'message': 'Order updated successfully',
                        'order': result.data[0]
                    }, status=status.HTTP_200_OK)
            
            return Response({
                'message': 'No changes made'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': f'An error occurred while updating order: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def cancel_order(self, request, order_id):
        """
        Cancel an order (only if pending)
        """
        try:
            user_id = get_user_id_from_token(request)
            if not user_id:
                return Response({
                    'error': 'Invalid or missing authentication token'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            # Check if order exists and belongs to user
            existing_order = supabase.table('orders').select('*').eq('id', order_id).eq('user_id', user_id).execute()
            if not existing_order.data:
                return Response({
                    'error': 'Order not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            order = existing_order.data[0]
            
            if order.get('status') != 'pending':
                return Response({
                    'error': 'Order cannot be cancelled'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get order items to restore stock
            items_result = supabase.table('order_items').select('''
                *,
                product:product_id(id, stock)
            ''').eq('order_id', order_id).execute()
            
            # Restore product stock
            for item in items_result.data:
                product = item.get('product', {})
                quantity = item.get('quantity', 0)
                current_stock = product.get('stock', 0)
                new_stock = current_stock + quantity
                
                supabase.table('product').update({
                    'stock': new_stock
                }).eq('id', product.get('id')).execute()
            
            # Update order status
            result = supabase.table('orders').update({
                'status': 'cancelled'
            }).eq('id', order_id).execute()
            
            return Response({
                'message': 'Order cancelled successfully'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': f'An error occurred while cancelling order: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)