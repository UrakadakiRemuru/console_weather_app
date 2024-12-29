from datetime import datetime
from typing import Dict

import pytz
from googletrans import Translator
from weather_console.services.prepare_data import METRICS_MAP

def get_translator() -> Translator:
    '''
    Получение экземпляра переводчика.

    Raises:
        ConnectionError: В случае если возникли проблемы с подключением к сервису переводчика.

    Returns:
        экземпляр переводчика.
    '''
    try:
        return Translator()
    except ConnectionError as e:
        raise ConnectionError('Произошла ошибка подключения к сервису.'
                              ' Проверьте подключение к интернету и повторите попытку позже.') from e


def prepare_weather_data_to_representation(weather_data: Dict[str, str | float | int],
                                           coordinates: Dict[str, str | float | int],
                                           units_code: str) -> Dict[str, str]:
    '''
    Добавляет название города из ответа от geocoding в отформатированный словарь ответа от OWM и возвращает измененный
    словарь.

    Args:
        weather_data (Dict[str, str | float | int]): Отформатированный словарь ответа от OWM.
        coordinates (Dict[str, str | float | int]): Отформатированный словарь ответа от geocoding.
        units_code (str): Код системы единиц измерения.

    Returns:
        Словарь с данными о погоде.

    Examples:
        {
            'city': ...,
            'time': ...,
            'temperature': ...,
            'feels_like': ...,
            'wind_speed': ...,
        }
    '''

    temp = METRICS_MAP.get('temperature').get(units_code)
    speed = METRICS_MAP.get('speed').get(units_code)

    city_name = coordinates.get('city')
    weather_data['temperature'] = str(weather_data['temperature']) + temp
    weather_data['feels_like'] = str(weather_data['feels_like']) + temp
    weather_data['wind_speed'] = str(weather_data['wind_speed']) + speed
    return {
        'city': city_name,
        'time': str(datetime.now(pytz.timezone('Europe/Moscow'))),
        **weather_data
    }
