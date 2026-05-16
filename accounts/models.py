from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
import uuid


class CustomUser(AbstractUser):
    full_name = models.CharField(max_length=150, default="Nombre completo")
    birth_date = models.DateField(default="2000-01-01")
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    wallet_balance = models.IntegerField(default=0)
    gifs_unlocked = models.BooleanField(default=False)
    # Marco equipado actualmente (nombre del archivo, ej: "marco1.png")
    equipped_frame = models.CharField(max_length=100, blank=True, null=True, default=None)

    def __str__(self):
        return self.username


class UserFrame(models.Model):
    """Mochila de cosméticos: marcos adquiridos por el usuario."""
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='frames')
    frame_name = models.CharField(max_length=100)  # Ej: "marco1.png"
    purchased_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'frame_name')

    def __str__(self):
        return f"{self.user.username} – {self.frame_name}"


class Achievement(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.CharField(max_length=20, default="🏆")
    
    # "tasks", "shopping", "points", "houses", "messages"
    condition_type = models.CharField(max_length=50)
    target_value = models.IntegerField(default=1)
    
    # Saldo a dar
    reward_saldo = models.IntegerField(default=10)
    
    def __str__(self):
        return self.name


class UserAchievement(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='achievements')
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    earned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'achievement')

    def __str__(self):
        return f"{self.user.username} logró {self.achievement.name}"


