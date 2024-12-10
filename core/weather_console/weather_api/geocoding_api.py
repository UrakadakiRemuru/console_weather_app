import os
from typing import Dict, List

import requests
from dotenv import load_dotenv
from googletrans import Translator

from weather_console.weather_by_name.weather_by_name import translate_anything, get_translated_country_name_by_code

load_dotenv()

API_KEY = os.getenv('OWM_API_KEY')


def get_city_coordinates(literal_name: Dict[str, str]) -> Dict[str, float | str | dict[str, str]]:
    '''
    Получение координат города через geocoding-api.
    Args:
        literal_name (dict[str, str]): Словарь с наименованием города и кода страны или наименованием города.
        {'city': val, 'country_code': val}

    Raises:
        ConnectionError: В случае проблем подключения к интернету или проблем на стороне сервиса.
        TimeoutError: В случае проблем подключения к сервису.
        ValueError: В случае если пользователь ввел некорректные данные.

    Returns:
        Список словарей с названием города, кодом страны, а также широтой и долготой.

    '''

    city_name = literal_name.get('city')
    country_code = literal_name.get('country_code') or ''

    params = {
        'q': f'{city_name},{country_code}',
        'limit': 5,
        'appid': API_KEY
    }

    try:
        response = requests.get('http://api.openweathermap.org/geo/1.0/direct', params=params, timeout=5)
    except ConnectionError as e:
        raise ConnectionError('Проверьте подключение к интернету и повторите попытку.') from e
    except TimeoutError as e:
        raise TimeoutError('Проблемы соединения с сервисом. Повторите попытку позже') from e

    if response.status_code == 200:
        response = response.json()
        if not response:
            raise ValueError(f'К сожалению данные о погоде не были получены.'
                             f'Проверьте введенные данные "{city_name}" и повторите запрос.')
        return response

    raise ConnectionError('Произошла проблема на стороне сервиса. Попробуйте повторить попытку позже.')


def parse_response(response: List[Dict], lang_preference: str = 'ru', *, translator: Translator) -> List[
    Dict[str, float | str | None]]:
    '''

    Args:
        response (list[dict]): Данные, полученные в ответе.
        lang_preference (str): ISO-3166 код предпочитаемого языка.
        translator (Translator): Экземпляр переводчика.

    Returns:
        Список словарей следующего формата:
        [
            {
                'name': название города (str),
                'state': область (str)
                'country': название страны (str),
                'lat': широта (float),
                'lon': долгота (float)
            }
        ]
    '''

    lang_preference = lang_preference.lower()

    parsed_list = []

    for city_dict in response:
        current_city_info = {}

        local_names = city_dict.get('local_names')
        if not local_names:
            continue

        current_city_info['name'] = local_names.get(lang_preference)

        current_city_info.update({
            'country_code': get_translated_country_name_by_code(city_dict.get('country'), lang_preference,
                                                                translator=translator),
            'lat': city_dict.get('lat'),
            'lon': city_dict.get('lon'),
        })

        state = city_dict.get('state')
        if state == city_dict.get('name'):
            state = current_city_info['name']
        elif state:
            state = translate_anything(state, lang_preference, translator=translator)

        current_city_info.update({'state': state})

        parsed_list.append(current_city_info)

    return parsed_list
