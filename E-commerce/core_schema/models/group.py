from django.db import models
from .timestamp import TimeStamp

class CustomGroup(TimeStamp):
    group_name = models.CharField(max_length=50, unique=True)
    permissions = models.ManyToManyField('Permission', blank=True, related_name='custom_groups')

    def __str__(self):
        return self.group_name

    class Meta:
        db_table = 'custom_group'
        ordering = ['group_name']   