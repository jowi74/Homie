from django.db import models
from django.conf import settings
from houses.models import House

class ShoppingItem(models.Model):
    house = models.ForeignKey(House, on_delete=models.CASCADE, related_name='shopping_items')
    name = models.CharField(max_length=100)
    quantity = models.CharField(max_length=50, blank=True, null=True)  # Ej: "2", "500g", "1 bolsa"
    is_checked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.house.name}"

class CustomReward(models.Model):
    CURRENCY_CHOICES = [
        ('points', 'Puntos comunes'),
        ('saldo', 'Saldo personal'),
    ]

    house = models.ForeignKey(House, on_delete=models.CASCADE, related_name='custom_rewards')
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_rewards')
    title = models.CharField(max_length=150)
    description = models.TextField()
    image = models.ImageField(upload_to='custom_rewards/', blank=True, null=True)
    price = models.IntegerField(default=50)
    currency_type = models.CharField(max_length=10, choices=CURRENCY_CHOICES, default='points')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.price} {self.currency_type}) - {self.house.name}"


class Purchase(models.Model):
    CURRENCY_CHOICES = [
        ('puntos', 'Puntos comunes'),
        ('saldo', 'Saldo personal'),
    ]

    house = models.ForeignKey(House, on_delete=models.CASCADE, related_name='purchases')
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='purchases')
    item_name = models.CharField(max_length=200)
    currency_type = models.CharField(max_length=10, choices=CURRENCY_CHOICES)
    amount = models.IntegerField()
    is_custom_reward = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.buyer.username} compró {self.item_name} ({self.amount} {self.currency_type})"
