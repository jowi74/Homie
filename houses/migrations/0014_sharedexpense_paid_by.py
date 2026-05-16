from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('houses', '0013_houseevent_sharedexpense'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='sharedexpense',
            name='paid_by',
            field=models.ManyToManyField(
                blank=True,
                related_name='confirmed_expenses',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
