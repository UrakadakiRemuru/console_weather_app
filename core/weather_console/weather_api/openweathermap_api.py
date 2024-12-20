import os
from typing import Dict
from dotenv import load_dotenv

import requests
from requests import exceptions

load_dotenv()

def get_weather_data(lat:float, lon:float, units: str, lang_preference: str) -> Dict:
    '''
    Получение данных о погоде из openweathermap.
    Args:
        lat (float): Широта.
        lon (float): Долгота.
        units (str): Единицы измерения.
        lang_preference (str): ISO-3166 код страны предпочитаемого языка.

    Raises:
        ConnectionError: В случае если присутствуют проблемы с интернет-соединением.
        TimeoutError: В случае проблем подключения к сервису.

    Returns:
        Данные о погоде в виде словаря.
    '''

    if units:
        units = units.lower()
    else:
        units = 'metric'

    if lang_preference:
        lang_preference = lang_preference.lower()
    else:
        lang_preference = 'ru'

    params = {
        'lat': lat,
        'lon': lon,
        'appid': os.getenv('OWM_API_KEY'),
        'units': units,
        'exclude': 'minutely,hourly,daily,alerts',
        'lang': lang_preference,
    }

    try:
        response = requests.get('https://api.openweathermap.org/data/2.5/weather', params=params, timeout=5)
    except exceptions.ConnectionError as e:
        raise ConnectionError('Проверьте подключение к интернету и повторите попытку.') from e
    except (exceptions.Timeout, exceptions.ReadTimeout) as e:
        raise TimeoutError('Проблемы соединения с сервисом. Повторите попытку позже') from e

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
        'temperature': int(data.get('main').get('temp')),
        'feels_like': int(data.get('main').get('feels_like')),
        'wind_speed': data.get('wind').get('speed'),
    }
