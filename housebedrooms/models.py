from django.db import models
from accounts.models import CustomUser
from houses.models import House

WALL_COLORS = [
    ('#d6c3a3', 'Madera Clásica'),
    ('#b8d4e8', 'Azul Cielo'),
    ('#c8e6c9', 'Verde Menta'),
    ('#f8bbd0', 'Rosa Suave'),
    ('#e8d5b7', 'Crema Cálida'),
    ('#d1c4e9', 'Lavanda'),
]

RUG_STYLES = [
    ('rug_default', 'Alfombra Clásica'),
    ('rug_stars', 'Alfombra de Estrellas'),
]

POSTER_STYLES = [
    ('none', 'Sin Poster'),
    ('poster_gaming', 'Poster Gaming'),
]

class HouseProfile(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='house_profiles')
    house = models.ForeignKey(House, on_delete=models.CASCADE, related_name='house_profiles')
    points = models.PositiveIntegerField(default=0)
    completed_tasks_count = models.PositiveIntegerField(default=0)
    completed_shopping_count = models.PositiveIntegerField(default=0)
    
    # Personalización del dormitorio
    bedroom_wallcolor = models.CharField(max_length=20, default='#d6c3a3')
    bedroom_rug_style = models.CharField(max_length=30, default='rug_default')
    bedroom_poster = models.CharField(max_length=30, default='none')

    # Ítems desbloqueados desde la tienda
    unlock_wallcolor = models.BooleanField(default=False)
    unlock_stars_rug = models.BooleanField(default=False)
    unlock_poster_gaming = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'house')

    def __str__(self):
        return f"{self.user.username} en {self.house.name} - {self.points} pts"

class PrivateNickname(models.Model):
    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='given_nicknames')
    target_user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='received_nicknames')
    house = models.ForeignKey(House, on_delete=models.CASCADE, related_name='nicknames')
    nickname = models.CharField(max_length=50)

    class Meta:
        unique_together = ('owner', 'target_user', 'house')

    def __str__(self):
        return f"{self.owner.username} llama a {self.target_user.username} '{self.nickname}' en {self.house.name}"
