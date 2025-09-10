from django.db import models
from .timestamp import TimeStamp
from django.contrib.auth import  get_user_model # Importing User model from Django's auth system

user = get_user_model()
class ProductOptions(TimeStamp):
    option_name = models.CharField(max_length=100)
    option_price = models.IntegerField()
    option_description = models.CharField(max_length=255)
    stock = models.IntegerField()
    product_id = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='product_options')
    user_id = models.ForeignKey(user, on_delete=models.CASCADE, related_name='product_options')

    def __str__(self):
        return f"{self.option_name} - {self.product_id.name}"

    class Meta:
        db_table = 'product_options'
        ordering = ['product_id', 'option_name']
