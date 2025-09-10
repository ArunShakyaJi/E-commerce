from django.db import models
from .timestamp import TimeStamp
from django.contrib.auth import  get_user_model # Importing User model from Django's auth system

user = get_user_model()
class Review(TimeStamp):
    review = models.TextField()
    rating = models.IntegerField(default=5)  # 1-5 star rating
    user_id = models.ForeignKey(user, on_delete=models.CASCADE, related_name='reviews')
    product_id = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='reviews')

    def __str__(self):
        return f"Review by {self.user_id.username} for {self.product_id.name} - {self.rating}★"

    class Meta:
        db_table = 'review'
        ordering = ['-id']  # Orders by id in descending order