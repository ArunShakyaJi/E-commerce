from django.db import models

class User(models.Model):
    id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=50, unique=True)
    password = models.CharField(max_length=128)  # Store hashed passwords
    email = models.EmailField(max_length=100, unique=True)
    role = models.ForeignKey('core_schema.Roles', on_delete=models.SET_NULL, null=True, blank=True, related_name='users')

    def __str__(self):
        return self.username

    class Meta:
        db_table = 'user'
        ordering = ['username']