from django.db import models
from .timestamp import TimeStamp

class OrderItems(TimeStamp):
    order_id = models.ForeignKey('Order', on_delete=models.CASCADE, related_name='order_items')
    product_id = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='order_items')
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"OrderItem {self.id} for Order {self.order_id}"

    class Meta:
        db_table = 'order_items'
        ordering = ['order_id', 'product_id']