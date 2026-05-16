from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('shopping', '0002_customreward'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('houses', '0009_house_spent_points'),
    ]

    operations = [
        migrations.CreateModel(
            name='Purchase',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('item_name', models.CharField(max_length=200)),
                ('currency_type', models.CharField(choices=[('puntos', 'Puntos comunes'), ('saldo', 'Saldo personal')], max_length=10)),
                ('amount', models.IntegerField()),
                ('is_custom_reward', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('buyer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='purchases', to=settings.AUTH_USER_MODEL)),
                ('house', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='purchases', to='houses.house')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
