from django.db import models
from django.utils.text import slugify
from accounts.models import CustomUser

class House(models.Model):
    name = models.CharField(max_length=100) #nombre de la casa
    description = models.TextField(blank=True)  #descripcion de la casa
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    image = models.ImageField(upload_to='house_images/', null=True, blank=True)  #foto de la casa(opcional)
    members = models.ManyToManyField(CustomUser, related_name='houses')
    creator = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='created_houses', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Campo temporal para guardar código de eliminación
    deletion_code = models.CharField(max_length=6, blank=True, null=True)
    
    # Campo para desbloquear gifs en foto de grupo y de casa
    gifs_unlocked = models.BooleanField(default=False)
    
    # Campo para almacenar los puntos totales gastados por la casa en la tienda
    spent_points = models.IntegerField(default=0)

    @property
    def available_points(self):
        from housebedrooms.models import HouseProfile
        total_earned = sum(p.points for p in HouseProfile.objects.filter(house=self))
        return total_earned - self.spent_points

    def get_admin(self):
        return self.creator

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while House.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

class HouseNote(models.Model):
    house = models.ForeignKey(House, on_delete=models.CASCADE, related_name='notes')
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='house_notes')
    content = models.TextField()
    color = models.CharField(max_length=20, default="#ffffcc")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Nota de {self.author.username} en {self.house.name}"

class PersonalDiaryEntry(models.Model):
    house = models.ForeignKey(House, on_delete=models.CASCADE, related_name='diary_entries')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='diary_entries')
    title = models.CharField(max_length=100)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Entrada de {self.user.username} - {self.title}"

class Reminder(models.Model):
    house = models.ForeignKey(House, on_delete=models.CASCADE, related_name='reminders')
    creator = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='created_reminders')
    message = models.CharField(max_length=255)
    trigger_time = models.DateTimeField()
    target_user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True, related_name='reminders')
    read_by = models.ManyToManyField(CustomUser, blank=True, related_name='read_reminders')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.house.name} - Hora: {self.trigger_time} - {self.message}"


class ChatRoom(models.Model):
    house = models.ForeignKey(House, on_delete=models.CASCADE, related_name='chat_rooms')
    name = models.CharField(max_length=150, null=True, blank=True)
    slug = models.SlugField(max_length=150, null=True, blank=True)
    is_group = models.BooleanField(default=False)
    members = models.ManyToManyField(CustomUser, related_name='chat_rooms')
    creator = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_chat_rooms')
    image = models.ImageField(upload_to='group_images/', null=True, blank=True)
    muted_members = models.ManyToManyField(CustomUser, related_name='muted_chat_rooms', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.is_group:
            return f"Grupo: {self.name} ({self.house.name})"
        return f"Privado - {self.house.name}"


class Message(models.Model):
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    # Soporte futuro para imágenes o archivos:
    # file = models.FileField(upload_to='chat_files/', null=True, blank=True)

    def __str__(self):
        return f"De {self.sender.username} - Sala {self.room.id}"

class SharedExpense(models.Model):
    house = models.ForeignKey(House, on_delete=models.CASCADE, related_name='expenses')
    payer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='paid_expenses')
    title = models.CharField(max_length=150)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    paid_by = models.ManyToManyField(CustomUser, related_name='confirmed_expenses', blank=True)

    def __str__(self):
        return f"{self.title}: {self.amount}€ por {self.payer.username}"

class HouseEvent(models.Model):
    house = models.ForeignKey(House, on_delete=models.CASCADE, related_name='events')
    creator = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='created_events')
    title = models.CharField(max_length=150)
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Evento: {self.title} el {self.date}"