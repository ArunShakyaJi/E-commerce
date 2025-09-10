from django.db import models
from .timestamp import TimeStamp
from django.contrib.auth import  get_user_model # Importing User model from Django's auth system

user = get_user_model()
class Category(TimeStamp):
    category_name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)
    user_id = models.ForeignKey( user, on_delete=models.CASCADE, blank=True, null=True, related_name='categories')

    def __str__(self):
        return self.category_name

    class Meta:
        db_table = 'category'
        ordering = ['category_name']