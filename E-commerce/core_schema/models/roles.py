from django.db import models
from .timestamp import TimeStamp

class Roles(TimeStamp):
    role_name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.role_name

    class Meta:
        db_table = 'roles'
        ordering = ['role_name']

# Note: RoleGroup relationship temporarily removed due to Django lazy reference issues
# You can manually manage the relationship through queries or create it later