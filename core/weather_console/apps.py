from django.apps import AppConfig
from django.db.models.signals import post_migrate
from django.dispatch import receiver


class WeatherConsoleConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'weather_console'

    def ready(self):
        from .models import UserPreferences

        @receiver(post_migrate)
        def create_user_preferences(sender, **kwargs):
            if not UserPreferences.objects.exists():
                UserPreferences.objects.create(is_first_time=True)
