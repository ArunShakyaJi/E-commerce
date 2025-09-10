from django.db import models

class TimeStamp(models.Model):
    id = models.AutoField(primary_key=True)
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    extradata = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"Created at: {self.created_at}, Updated at: {self.updated_at}"

    class Meta:
        abstract = True  # This makes it an abstract base class
        ordering = ['-created_at']  # Order by created_at in descending order