from django.db import models
from .timestamp import TimeStamp

class Images(TimeStamp):
    image_name = models.CharField(max_length=100, unique=True)
    image_url = models.URLField(max_length=200, unique=True)
    alt_text = models.CharField(max_length=255, blank=True, null=True)    
    user_id = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='images')
    def __str__(self):
        return self.image_name

    class Meta:
        db_table = 'images'
        ordering = ['image_name']