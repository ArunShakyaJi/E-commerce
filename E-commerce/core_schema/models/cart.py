from django.db import models
from .timestamp import TimeStamp
from django.contrib.auth import  get_user_model # Importing User model from Django's auth system

user = get_user_model()  # This will dynamically get the User model, which is useful for custom user models
class Cart(TimeStamp):
    user_id = models.ForeignKey(user, on_delete=models.CASCADE, related_name='cart_items')
    product_id = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='cart_items')
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Cart {self.id} for User {self.user_id}"

    class Meta:
        db_table = 'cart'
        ordering = ['user_id', 'product_id']
        unique_together = ('user_id', 'product_id')  # Ensures a user can only have one entry per product