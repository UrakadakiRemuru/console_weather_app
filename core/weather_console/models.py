from typing import List, Tuple

from django.db import models


class UserRequestHistory(models.Model):
    city = models.CharField(max_length=255, null=True)
    country = models.CharField(max_length=255, null=True)
    is_current_location = models.BooleanField(default=False)
    counter = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    objects = models.Manager()

    class Meta:
        db_table = 'user_request_history'
        managed = True


class RequestParamsToOpenWeather(models.Model):
    latitude = models.FloatField()
    longitude = models.FloatField()
    request_time = models.DateTimeField(auto_now=True)

    objects = models.Manager()

    class Meta:
        db_table = 'request_params_to_openweather'
        managed = True


class ResponseFromOpenWeather(models.Model):
    weather = models.CharField(max_length=255)
    temperature = models.IntegerField()
    feels_like = models.IntegerField()
    wind_speed = models.FloatField()
    response_time = models.DateTimeField(auto_now_add=True)

    objects = models.Manager()

    class Meta:
        db_table = 'response_from_openweather'
        managed = True


class RequestResponseConnection(models.Model):
    user_request = models.ForeignKey(UserRequestHistory, on_delete=models.CASCADE)
    request = models.ForeignKey(RequestParamsToOpenWeather, on_delete=models.CASCADE)
    response = models.ForeignKey(ResponseFromOpenWeather, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now=True)
    objects = models.Manager()

    class Meta:
        db_table = 'request_response_connection'
        managed = True


class UserPreferences(models.Model):
    UNITS_CHOICES = [
        ('standard', 'как на физике'),
        ('metric', 'метрическая'),
        ('imperial', 'имперская'),
    ]

    LANGUAGE_CHOICES = [
        ('RU', 'русский'),
        ('EN', 'английский'),
        ('ES', 'испанский')
    ]

    is_first_time = models.BooleanField(default=True)
    language = models.CharField(max_length=2, choices=LANGUAGE_CHOICES, default='RU')
    units = models.CharField(max_length=8, choices=UNITS_CHOICES, default='metric')
    instruction_on_start = models.BooleanField(default=True)

    objects = models.Manager()

    @property
    def language_display(self):
        '''Отображает словесное представление выбранного языка. '''
        return dict(self.LANGUAGE_CHOICES).get(self.language).capitalize()

    @property
    def units_display(self):
        '''Отображает словесное представление выбранных единиц измерения.'''
        return dict(self.UNITS_CHOICES).get(self.units).capitalize()

    def save_from_display(self, choices: List[Tuple[str, str]], attr_name: str):
        '''
        Сохраняет в значение атрибута с именем attr_name кодовое значение из choices.

        Args:
            choices (List[Tuple[str, str]]): Список кортежей вида (кодовое значение, имя для представления).
            attr_name (str): Имя поля.
        '''

        attr = getattr(self, attr_name)
        if attr not in dict(choices):
            for code, display in choices:
                if attr == display:
                    setattr(self, attr_name, code)
                    break

    def _validate_language(self):
        if self.language not in dict(self.LANGUAGE_CHOICES):
            raise ValueError('Вы ввели неподдерживаемый язык.')

    def _validate_units(self):
        if self.units not in dict(self.UNITS_CHOICES):
            raise ValueError('Вы ввели неподдерживаемую единицу измерения.')

    def save(self, *args, **kwargs):
        self.save_from_display(self.LANGUAGE_CHOICES, 'language')
        self._validate_language()
        self.save_from_display(self.UNITS_CHOICES, 'units')
        self._validate_units()
        super().save(*args, **kwargs)

    class Meta:
        db_table = 'user_preferences'
        managed = True
