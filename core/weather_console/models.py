from django.db import models


class UserRequestHistory(models.Model):
    city = models.CharField(max_length=255)
    country = models.CharField(max_length=255, null=True)
    is_current_location = models.BooleanField(default=False)
    counter = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_request_history'
        managed = True


class RequestParamsToOpenWeather(models.Model):
    latitude = models.FloatField()
    longitude = models.FloatField()
    request_time = models.DateTimeField()

    class Meta:
        db_table = 'request_params_to_openweather'
        managed = True


class ResponseFromOpenWeather(models.Model):
    weather = models.CharField(max_length=255)
    temperature = models.IntegerField()
    feels_like = models.IntegerField()
    wind_speed = models.FloatField()
    response_time = models.DateTimeField()

    class Meta:
        db_table = 'response_from_openweather'
        managed = True


class RequestResponseConnection(models.Model):
    user_request = models.ForeignKey(UserRequestHistory, on_delete=models.CASCADE)
    request = models.ForeignKey(RequestParamsToOpenWeather, on_delete=models.CASCADE)
    response = models.ForeignKey(ResponseFromOpenWeather, on_delete=models.CASCADE)

    class Meta:
        db_table = 'request_response_connection'
        managed = True


class UserPreferences(models.Model):

    UNITS_CHOICES = [
        ('standard', 'Как на физике'),
        ('metric', 'Метрическая'),
        ('imperial', 'Имперская'),
    ]

    is_first_time = models.BooleanField(default=True)
    language = models.CharField(max_length=2, default='RU')
    units = models.CharField(max_length=8, choices=UNITS_CHOICES, default='metric')
    instruction_on_start = models.BooleanField(default=True)

    class Meta:
        db_table = 'user_preferences'
        managed = True
