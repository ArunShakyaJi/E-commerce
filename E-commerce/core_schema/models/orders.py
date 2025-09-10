from django.db import models
from .timestamp import TimeStamp
from decimal import Decimal
from django.contrib.auth import  get_user_model # Importing User model from Django's auth system

user = get_user_model()

class Order(TimeStamp):
    order_number = models.CharField(max_length=100, unique=True)
    user_id = models.ForeignKey(user, on_delete=models.CASCADE, related_name='orders')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    status = models.CharField(max_length=50, default='pending')

    def __str__(self):
        return f"Order {self.order_number} by User {self.user_id}"

    class Meta:
        db_table = 'orders'
        ordering = ['-id']  # Orders by order_date in descending order