from django.db import models
from houses.models import House
from accounts.models import CustomUser

class Task(models.Model):
    house = models.ForeignKey(House, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=150)
    assigned_to = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tasks')
    points = models.PositiveIntegerField(default=10)
    is_completed = models.BooleanField(default=False)
    has_been_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.house.name}"
