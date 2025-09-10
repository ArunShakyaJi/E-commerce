from django.db import models
from .timestamp import TimeStamp

class Permission(TimeStamp):
    permission_name = models.CharField(max_length=50, unique=True)
    type = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.permission_name

    class Meta:
        db_table = 'permission'
        ordering = ['permission_name']