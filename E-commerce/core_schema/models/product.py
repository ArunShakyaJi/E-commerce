from django.db import models
from .timestamp import TimeStamp
from django.contrib.auth import  get_user_model # Importing User model from Django's auth system

user = get_user_model()
class Product(TimeStamp):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    category = models.ForeignKey('Category', on_delete=models.CASCADE, related_name='products')
    image = models.ForeignKey('Images', on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    user_id = models.ForeignKey(user, on_delete=models.CASCADE, related_name='products')

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'product'
        ordering = ['-created_at']