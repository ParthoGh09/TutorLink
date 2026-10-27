from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('notification_type', models.CharField(choices=[('MATCH', 'Match'), ('APPLICATION', 'Application'), ('DEMO', 'Demo'), ('VERIFICATION', 'Verification'), ('LOCATION', 'Location'), ('REVIEW', 'Review'), ('SYSTEM', 'System')], default='SYSTEM', max_length=20)),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField()),
                ('link', models.CharField(blank=True, max_length=255, null=True)),
                ('is_read', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('recipient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['is_read', '-created_at'],
            },
        ),
    ]
