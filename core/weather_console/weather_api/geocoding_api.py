import os
from typing import Dict, List, Tuple

import requests
from dotenv import load_dotenv
from googletrans import Translator
from requests import exceptions
from weather_console.weather_by_name.weather_by_name import translate_anything, get_translated_country_name_by_code

load_dotenv()

API_KEY = os.getenv('OWM_API_KEY')


def get_city_coordinates(names_map: Dict[str, str]) -> Dict[str, float | str | dict[str, str]]:
    '''
    Получение координат города через geocoding-api.
    Args:
        names_map (dict[str, str]): Словарь с наименованием города и кода страны или наименованием города.
        {'city': val, 'country_code': val}

    Raises:
        ConnectionError: В случае проблем подключения к интернету или проблем на стороне сервиса.
        TimeoutError: В случае проблем подключения к сервису.
        ValueError: В случае если пользователь ввел некорректные данные.

    Returns:
        Список словарей с названием города, кодом страны, а также широтой и долготой.

    '''

    city_name = names_map.get('city')
    country_code = names_map.get('country_code') or ''

    params = {
        'q': f'{city_name},{country_code}',
        'limit': 5,
        'appid': API_KEY
    }

    try:
        response = requests.get('http://api.openweathermap.org/geo/1.0/direct', params=params, timeout=5)
    except exceptions.ConnectionError as e:
        raise ConnectionError('Проверьте подключение к интернету и повторите попытку.') from e
    except (exceptions.Timeout, exceptions.ReadTimeout) as e:
        raise TimeoutError('Проблемы соединения с сервисом. Повторите попытку позже') from e

    if response.status_code == 200:
        response = response.json()
        if not response:
            raise ValueError(f'К сожалению данные о погоде не были получены.'
                             f'Проверьте введенные данные "{city_name}" и повторите запрос.')
        return response

    raise ConnectionError('Произошла проблема на стороне сервиса. Попробуйте повторить попытку позже.')


def get_city_coordinates_reversed(lat: float, lon: float) -> Dict[str, float | str | dict[str, str]]:
    '''
    Получение ответа geocoding-api по координатам.

    Args:
        lat (float): Широта.
        lon (float): Долгота.

    Raises:
        ConnectionError: В случае проблем подключения к интернету или проблем на стороне сервиса.
        TimeoutError: В случае проблем подключения к сервису.

    Returns:
        Список словарей с названием города, кодом страны, а также широтой и долготой.

    '''

    params = {
        'lat': lat,
        'lon': lon,
        'limit': 1,
        'appid': API_KEY
    }

    try:
        response = requests.get('http://api.openweathermap.org/geo/1.0/reverse', params=params, timeout=5)
    except exceptions.ConnectionError as e:
        raise ConnectionError('Проверьте подключение к интернету и повторите попытку.') from e
    except (exceptions.Timeout, exceptions.ReadTimeout) as e:
        raise TimeoutError('Проблемы соединения с сервисом. Повторите попытку позже') from e

    if response.status_code == 200:
        return response.json()

    raise ConnectionError('Произошла проблема на стороне сервиса. Попробуйте повторить попытку позже.')

def parse_geocoding_response(response: List[Dict], lang_preference: str, *, translator: Translator) -> List[
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
                'city': название города (str),
                'state': область (str)
                'country': название страны (str),
                'country_code': код страны в ISO-3166 (str),
                'lat': широта (float),
                'lon': долгота (float)
            }
        ]
    '''
    if lang_preference:
        lang_preference = lang_preference.lower()
    else:
        lang_preference = 'ru'

    parsed_list = []

    static_city_name = ''

    for city_dict in response:
        current_city_info = {}

        local_names = city_dict.get('local_names')
        if not local_names:
            continue

        city_name = local_names.get(lang_preference)

        if city_name:
            static_city_name = city_name

        current_city_info['city'] = static_city_name

        country_code = city_dict.get('country')

        current_city_info.update({
            'country': get_translated_country_name_by_code(country_code, lang_preference,
                                                           translator=translator),
            'country_code': country_code,
            'lat': city_dict.get('lat'),
            'lon': city_dict.get('lon'),
        })

        state = city_dict.get('state')
        if state == city_dict.get('city'):
            state = current_city_info['city']
        elif state:
            state = translate_anything(state, lang_preference, translator=translator)

        current_city_info.update({'state': state})

        parsed_list.append(current_city_info)

    return parsed_list


def get_coordinates_from_parsed_geocoding_response(parsed_geocoding_response: Dict[str, float | str | None]) -> Tuple[
    float,
    float]:

    '''
    Позволяет получить широту и долготу из данных о городе из ответа geocoding.

    Args:
        parsed_geocoding_response (Dict[str, float | str | None]): Данные о городе из ответа geocoding.

    Returns:
        Кортеж с координатами (широта, долгота).
    '''

    return (
        parsed_geocoding_response.get('lat'),
        parsed_geocoding_response.get('lon')
    )
