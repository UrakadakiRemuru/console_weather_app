from typing import Dict

from weather_console.models import RequestParamsToOpenWeather, UserRequestHistory, ResponseFromOpenWeather
from pytz import timezone

METRICS_MAP = {
    'temperature': {
        'standard': ' K',
        'metric': ' C°',
        'imperial': ' F',
    },
    'speed': {
        'standard': ' м / с',
        'metric': ' м / с',
        'imperial': ' мил / с',
    }
}

def prepare_request_data(request: RequestParamsToOpenWeather) -> Dict[str, str]:
    '''
    Предоставляет широту и долготу из экземпляра параметров запроса к OWM.
    Args:
        request (RequestParamsToOpenWeather): Экземпляр параметров запроса к OWM.

    Returns:
        Словарь с широтой и долготой.
        {'lat': 11.1, 'lon': 11.1}
    '''

    return {
        'lat': request.latitude,
        'lon': request.longitude
    }


def prepare_response_data(
        user_request: UserRequestHistory, response: ResponseFromOpenWeather, units_code: str) -> Dict[str, str]:
    '''
    Предоставляет данные о погоде.

    Args:
        user_request (UserRequestHistory): Экземпляр запроса пользователя.
        response (ResponseFromOpenWeather): Экземпляр ответа от OWM.
        units_code (str): Код системы единиц измерения.

    Returns:
        Данные о погоде.
    '''

    temp = METRICS_MAP.get('temperature').get(units_code)
    speed = METRICS_MAP.get('speed').get(units_code)

    dict_data = [
        ('city', user_request.city),
        ('time', response.response_time.astimezone(timezone('Europe/Moscow')).strftime('%H:%M:%S %d.%m.%Y')),
        ('temperature', str(response.temperature) + temp),
        ('feels_like', str(response.feels_like) + temp),
        ('wind_speed', str(response.wind_speed) + speed)
    ]

    return dict(dict_data)
