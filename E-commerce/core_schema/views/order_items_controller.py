from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from supabase import create_client, Client
from decouple import config
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
def order_items_list(request):
    """
    List order items for a specific order
    """
    try:
        user_id = get_user_id_from_token(request)
        if not user_id:
            return Response({
                'error': 'Invalid or missing authentication token'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        order_id = request.GET.get('order_id')
        
        if not order_id:
            return Response({
                'error': 'order_id parameter is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify order belongs to user
        order_result = supabase.table('orders').select('*').eq('id', order_id).eq('user_id', user_id).execute()
        if not order_result.data:
            return Response({
                'error': 'Order not found or not authorized'
            }, status=status.HTTP_404_NOT_FOUND)
        
        result = supabase.table('order_items').select('''
            *,
            product:product_id(id, name, price, image_id),
            order:order_id(id, status, total_amount)
        ''').eq('order_id', order_id).execute()
        
        return Response({
            'order_items': result.data,
            'order': order_result.data[0]
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': f'An error occurred while fetching order items: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def order_item_detail(request, item_id):
    """
    Get details of a specific order item
    """
    try:
        user_id = get_user_id_from_token(request)
        if not user_id:
            return Response({
                'error': 'Invalid or missing authentication token'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        result = supabase.table('order_items').select('''
            *,
            product:product_id(id, name, price, image_id),
            order:order_id!inner(id, status, total_amount, user_id)
        ''').eq('id', item_id).execute()
        
        if not result.data:
            return Response({
                'error': 'Order item not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        order_item = result.data[0]
        
        # Check if order belongs to user
        if order_item.get('order', {}).get('user_id') != user_id:
            return Response({
                'error': 'Not authorized to view this order item'
            }, status=status.HTTP_403_FORBIDDEN)
        
        return Response({
            'order_item': order_item
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': f'An error occurred while fetching order item: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class OrderItemsController(APIView):
    """
    Order Items Controller using Supabase for CRUD operations
    """
    
    @permission_classes([IsAuthenticated])
    def get(self, request):
        """
        List order items
        """
        return order_items_list(request)
    
    @permission_classes([IsAuthenticated])
    def post(self, request):
        """
        Add item to existing order (only if order is pending)
        """
        try:
            user_id = get_user_id_from_token(request)
            if not user_id:
                return Response({
                    'error': 'Invalid or missing authentication token'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            data = request.data
            
            required_fields = ['order_id', 'product_id', 'quantity']
            if not all(field in data for field in required_fields):
                return Response({
                    'error': f'Required fields: {", ".join(required_fields)}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            order_id = int(data['order_id'])
            product_id = int(data['product_id'])
            quantity = int(data['quantity'])
            
            if quantity <= 0:
                return Response({
                    'error': 'Quantity must be greater than 0'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if order exists, belongs to user, and is modifiable
            order_result = supabase.table('orders').select('*').eq('id', order_id).eq('user_id', user_id).execute()
            if not order_result.data:
                return Response({
                    'error': 'Order not found or not authorized'
                }, status=status.HTTP_404_NOT_FOUND)
            
            order = order_result.data[0]
            if order.get('status') != 'pending':
                return Response({
                    'error': 'Cannot modify order items for non-pending orders'
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
            
            # Check if item already exists in order
            existing_item = supabase.table('order_items').select('*').eq('order_id', order_id).eq('product_id', product_id).execute()
            
            if existing_item.data:
                return Response({
                    'error': 'Product already exists in this order. Use update instead.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            price = float(product.get('price', 0))
            total = price * quantity
            
            item_data = {
                'order_id': order_id,
                'product_id': product_id,
                'quantity': quantity,
                'price': price,
                'total': total
            }
            
            result = supabase.table('order_items').insert(item_data).execute()
            
            if result.data:
                # Update order total
                new_order_total = float(order.get('total_amount', 0)) + total
                supabase.table('orders').update({
                    'total_amount': new_order_total
                }).eq('id', order_id).execute()
                
                # Update product stock
                new_stock = product.get('stock', 0) - quantity
                supabase.table('product').update({
                    'stock': new_stock
                }).eq('id', product_id).execute()
                
                return Response({
                    'message': 'Order item added successfully',
                    'order_item': result.data[0]
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    'error': 'Failed to add order item'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except ValueError as e:
            return Response({
                'error': f'Invalid data format: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'error': f'An error occurred while adding order item: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def list_order_items(self, request):
        return self.get(request)
        
    def get_order_item(self, request, item_id):
        return order_item_detail(request, item_id)
        
    def add_order_item(self, request):
        return self.post(request)
        
    def update_order_item(self, request, item_id):
        """
        Update order item quantity (only if order is pending)
        """
        try:
            user_id = get_user_id_from_token(request)
            if not user_id:
                return Response({
                    'error': 'Invalid or missing authentication token'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            data = request.data
            
            # Get order item with order details
            item_result = supabase.table('order_items').select('''
                *,
                order:order_id!inner(id, status, total_amount, user_id),
                product:product_id(id, price, stock)
            ''').eq('id', item_id).execute()
            
            if not item_result.data:
                return Response({
                    'error': 'Order item not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            item = item_result.data[0]
            order = item.get('order', {})
            product = item.get('product', {})
            
            # Check authorization and order status
            if order.get('user_id') != user_id:
                return Response({
                    'error': 'Not authorized to modify this order item'
                }, status=status.HTTP_403_FORBIDDEN)
            
            if order.get('status') != 'pending':
                return Response({
                    'error': 'Cannot modify order items for non-pending orders'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if 'quantity' in data:
                new_quantity = int(data['quantity'])
                
                if new_quantity <= 0:
                    return Response({
                        'error': 'Quantity must be greater than 0'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                old_quantity = item.get('quantity', 0)
                quantity_diff = new_quantity - old_quantity
                
                # Check stock availability
                if quantity_diff > 0 and product.get('stock', 0) < quantity_diff:
                    return Response({
                        'error': 'Insufficient stock for quantity increase'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                price = float(product.get('price', 0))
                new_total = price * new_quantity
                old_total = float(item.get('total', 0))
                total_diff = new_total - old_total
                
                # Update order item
                update_result = supabase.table('order_items').update({
                    'quantity': new_quantity,
                    'total': new_total
                }).eq('id', item_id).execute()
                
                if update_result.data:
                    # Update order total
                    new_order_total = float(order.get('total_amount', 0)) + total_diff
                    supabase.table('orders').update({
                        'total_amount': new_order_total
                    }).eq('id', order.get('id')).execute()
                    
                    # Update product stock
                    new_stock = product.get('stock', 0) - quantity_diff
                    supabase.table('product').update({
                        'stock': new_stock
                    }).eq('id', product.get('id')).execute()
                    
                    return Response({
                        'message': 'Order item updated successfully',
                        'order_item': update_result.data[0]
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
                'error': f'An error occurred while updating order item: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def remove_order_item(self, request, item_id):
        """
        Remove order item (only if order is pending)
        """
        try:
            user_id = get_user_id_from_token(request)
            if not user_id:
                return Response({
                    'error': 'Invalid or missing authentication token'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            # Get order item with order details
            item_result = supabase.table('order_items').select('''
                *,
                order:order_id!inner(id, status, total_amount, user_id),
                product:product_id(id, stock)
            ''').eq('id', item_id).execute()
            
            if not item_result.data:
                return Response({
                    'error': 'Order item not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            item = item_result.data[0]
            order = item.get('order', {})
            product = item.get('product', {})
            
            # Check authorization and order status
            if order.get('user_id') != user_id:
                return Response({
                    'error': 'Not authorized to modify this order item'
                }, status=status.HTTP_403_FORBIDDEN)
            
            if order.get('status') != 'pending':
                return Response({
                    'error': 'Cannot modify order items for non-pending orders'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Remove order item
            delete_result = supabase.table('order_items').delete().eq('id', item_id).execute()
            
            # Update order total
            item_total = float(item.get('total', 0))
            new_order_total = float(order.get('total_amount', 0)) - item_total
            supabase.table('orders').update({
                'total_amount': new_order_total
            }).eq('id', order.get('id')).execute()
            
            # Restore product stock
            quantity = item.get('quantity', 0)
            new_stock = product.get('stock', 0) + quantity
            supabase.table('product').update({
                'stock': new_stock
            }).eq('id', product.get('id')).execute()
            
            return Response({
                'message': 'Order item removed successfully'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': f'An error occurred while removing order item: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
