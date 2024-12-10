import os
from typing import Dict
from dotenv import load_dotenv

import requests

load_dotenv()

def get_weather_data(lat:float, lon:float, units: str = 'metric', lang_preference: str = 'ru') -> Dict:
    '''
    Получение данных о погоде из openweathermap.
    Args:
        lat (float): Широта.
        lon (float): Долгота.
        units (str): Единицы измерения.
        lang_preference (str): ISO-3166 код страны предпочитаемого языка.

    Raises:
        ConnectionError: В случае если присутствуют проблемы с интернет-соединением.

    Returns:
        Данные о погоде в виде словаря.
    '''

    params = {
        'lat': lat,
        'lon': lon,
        'appid': os.getenv('OWM_API_KEY'),
        'units': units,
        'exclude': 'minutely,hourly,daily,alerts',
        'lang': lang_preference.lower(),
    }

    try:
        response = requests.get('https://api.openweathermap.org/data/2.5/weather', params=params, timeout=5)
    except ConnectionError as e:
        raise ConnectionError('Проверьте подключение к интернету и повторите попытку.') from e

    if response.status_code == 200:
        response = response.json()
        return response

    raise ConnectionError('Произошла проблема на стороне сервиса. Попробуйте повторить попытку позже.')


def parse_weather_data(data: Dict) -> Dict[str, str | float | int]:
    '''

    Преобразует словарь с данными о погоде в нужны формат.

    Args:
        data (dict): Словарь с данными о погоде.

    Returns:
        Отформатированный словарь.

    Examples:
        {
            'weather': ...,
            'temperature': ...,
            'feels_like': ...,
            'wind_speed': ...,
        }
    '''

    return {
        'weather': data.get('weather')[0].get('description').capitalize(),
        'temperature': data.get('main').get('temp'),
        'feels_like': data.get('main').get('feels_like'),
        'wind_speed': data.get('wind').get('speed'),
    }
