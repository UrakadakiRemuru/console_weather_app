from typing import Dict

from django.db import transaction
from django.db.models import QuerySet

from weather_console.models import (UserRequestHistory, RequestParamsToOpenWeather, ResponseFromOpenWeather,
                                    RequestResponseConnection, UserPreferences)
from weather_console.weather_api.geocoding_api import get_coordinates_from_parsed_geocoding_response


def _process_user_request(
        city_name: str = None,
        country_name: str = None,
        *,
        is_current_location: bool = False, ) -> UserRequestHistory:
    '''
    Создает или обновляет данные модели UserRequestHistory, исходя из данных
    введенных пользователем.

    Случай создания реализуется если в модели не присутствует
    ни одного совпадения с данными, введенными пользователем.

    Случай обновления реализуется, если в модели присутствуют схожие экземпляры.
    В данной ситуации происходит обновление полей counter (увеличивается на 1),
    также происходит данных о времени последнего запроса.

    Args:
        city_name (str): Наименование города.
        country_name (str): Наименование страны.
        is_current_location (bool): Маркер определения по текущей локации.

    Returns:
        Экземпляр пользовательского запроса.
    '''

    if is_current_location:
        user_request_instance, _ = UserRequestHistory.objects.get_or_create(
            city=city_name, country=country_name, is_current_location=is_current_location)
        user_request_instance.counter += 1
        user_request_instance.save()
        return user_request_instance

    try:
        user_request_instance = UserRequestHistory.objects.get(city=city_name, country=country_name,
                                                               is_current_location=is_current_location)
    except UserRequestHistory.DoesNotExist:
        return UserRequestHistory.objects.create(
            city=city_name,
            country=country_name,
            is_current_location=is_current_location,
            counter=1
        )

    user_request_instance.counter += 1
    user_request_instance.save()
    return user_request_instance


def _process_geocoding_api_response(latitude: float, longitude: float) -> RequestParamsToOpenWeather:
    '''
    Создает или получает экземпляр модели RequestParansToOpenWeather.

    Args:
        latitude (float): Широта.
        longitude (float): Долгота.

    Returns:
        Экземпляр параметров запроса к OW.
    '''
    instance, _ = RequestParamsToOpenWeather.objects.get_or_create(
        latitude=latitude,
        longitude=longitude
    )
    return instance


def _process_open_weather_map_response(
        weather_data: Dict[str, int | float]
) -> ResponseFromOpenWeather:
    '''
    Создает новый экземпляр модели ResponseFromOpenWeather.

    Args:
        weather_data (Dict[str, int | float]): Данные о погоде.

    Returns:
        Экземпляр ответа от OW.
    '''

    weather_data['temperature'] = int(weather_data.get('temperature'))
    weather_data['feels_like'] = int(weather_data.get('feels_like'))

    return ResponseFromOpenWeather.objects.create(**weather_data)


def _create_request_response_connection(
        user_request: UserRequestHistory,
        request: RequestParamsToOpenWeather,
        response: ResponseFromOpenWeather
):
    '''
    Создает экземпляр модели RequestResponseConnection. Связывает все инстансы между собой.

    Args:
        user_request (UserRequestHistory): Экземпляр пользовательского запроса.
        request (RequestParamsToOpenWeather): Экземпляр параметров запроса к OW.
        response (ResponseFromOpenWeather): Экземпляр ответа от OW.

    '''

    RequestResponseConnection.objects.create(
        user_request=user_request,
        request=request,
        response=response
    )


def fill_db(city_coordinates: Dict[str, float | str | None], parsed_weather_data: Dict[str, str | float | int],
            is_current_location: bool = False):
    '''
    Заполнение базы данных полученными данными в случае определения погоды по названию города.

    Args:
        city_coordinates (Dict[str, float | str | None]): Данные о городе.
        parsed_weather_data (Dict[str, str | float | int]): Данные о погоде.
        is_current_location (bool): Маркер для заполнения данных в текущей локации.

    '''

    with transaction.atomic():
        city_name = city_coordinates.get('city')
        country_name = city_coordinates.get('country')
        coords = get_coordinates_from_parsed_geocoding_response(city_coordinates)
        user_request_instance = _process_user_request(city_name, country_name, is_current_location=is_current_location)
        geocoding_api_response_instance = _process_geocoding_api_response(*coords)
        openweathermap_response_instance = _process_open_weather_map_response(parsed_weather_data)
        _create_request_response_connection(
            user_request=user_request_instance,
            request=geocoding_api_response_instance,
            response=openweathermap_response_instance
        )


def get_user_request_history() -> QuerySet[UserRequestHistory]:
    '''
    Получение множества экземпляров пользовательских запросов, отсортированных в убывающем порядке
    по количеству их частоты использования пользователем.

    Returns:
        Множество экземпляров пользовательских запросов.
    '''

    return UserRequestHistory.objects.all().order_by('-counter')


def get_user_request_instance(user_request_pk: int) -> UserRequestHistory:
    '''
    Предоставляет экземпляр пользовательского запроса по идентификатору.

    Args:
        user_request_pk (int): Идентификационный номер пользовательского запроса.

    Returns:
        Экземпляр пользовательского запроса.
    '''

    connection_instance = RequestResponseConnection.objects.filter(
        user_request=user_request_pk
    ).order_by('-created_at').first()
    return connection_instance.user_request


def get_request_instance_by_user_request(user_request_pk: int) -> RequestParamsToOpenWeather:
    '''
    Предоставляет экземпляр параметров запроса к OWM по идентификатору пользовательского запроса.

    Args:
        user_request_pk (int): Идентификационный номер пользовательского запроса.

    Returns:
        Экземпляр параметров запроса к OWM.
    '''

    connection_instance = RequestResponseConnection.objects.filter(
        user_request=user_request_pk
    ).order_by('-created_at').first()
    return connection_instance.request


def get_weather_instance_by_user_request(user_request_pk: int) -> ResponseFromOpenWeather:
    '''
    Предоставляет экземпляр ответа от OWM с информацией о погоде по идентификатору пользовательского запроса.

    Args:
        user_request_pk (int): Идентификационный номер пользовательского запроса.

    Returns:
        Экземпляр ответа от OWM.
    '''

    connection_instance = RequestResponseConnection.objects.filter(
        user_request=user_request_pk
    ).order_by('-created_at').first()
    return connection_instance.response


def increase_user_request_counter(user_request: UserRequestHistory):
    '''
    Увеличивает счетчик пользовательского запроса на 1.

    Args:
        user_request (UserRequestHistory): Экземпляр пользовательского запроса.
    '''

    user_request.counter += 1
    user_request.save()


def get_is_first_time() -> bool:
    '''
    Предоставляет поле is_first_time экземпляра настроек.

    Returns:
        Маркер первого запуска приложения.
    '''

    user_preferences_instance = _get_user_preferences_instance()
    return user_preferences_instance.is_first_time


def set_is_first_time(marker: bool):
    '''
    Устанавливает значение полю is_first_time экземпляру настроек.

    Args:
        marker (bool): Маркер первого запуска приложения.

    '''

    user_preferences_instance = _get_user_preferences_instance()
    user_preferences_instance.is_first_time = marker
    user_preferences_instance.save()


def get_instruction_on_start() -> bool:
    '''
    Предоставляет поле instruction_on_start экземпляра настроек.

    Returns:
        Маркер демонстрации настроек при запуске.
    '''

    user_preferences_instance = _get_user_preferences_instance()
    return user_preferences_instance.instruction_on_start


def set_instruction_on_start(marker: bool):
    '''
    Устанавливает значение полю instruction_on_start экземпляру настроек.

    Args:
        marker (bool): Маркер демонстрации настроек при запуске.

    '''

    user_preferences_instance = _get_user_preferences_instance()
    user_preferences_instance.instruction_on_start = marker
    user_preferences_instance.save()


def get_language_code() -> str:
    '''
    Предоставляет поле language экземпляра настроек.

    Returns:
        Код iso_3166 предпочитаемого языка.
    '''

    user_preferences_instance = _get_user_preferences_instance()
    return user_preferences_instance.language


def get_language() -> str:
    '''
    Предоставляет поле language экземпляра настроек.

    Returns:
        Словесное представление предпочитаемого языка.
    '''

    user_preferences_instance = _get_user_preferences_instance()
    return user_preferences_instance.language_display


def set_language(lang: str):
    '''
    Устанавливает значение полю language экземпляру настроек по словесному представлению языка.

    Args:
        lang (str): Словесное представление предпочитаемого языка. Один из: русский, английский, испанский.

    '''

    user_preferences_instance = _get_user_preferences_instance()
    user_preferences_instance.language = lang
    user_preferences_instance.save()


def get_units_code() -> str:
    '''
    Предоставляет поле units экземпляра настроек.

    Returns:
        Форма единиц измерения для передачи в запросы к API.
    '''

    user_preferences_instance = _get_user_preferences_instance()
    return user_preferences_instance.units


def get_units() -> str:
    '''
    Предоставляет поле units экземпляра настроек.

    Returns:
        Словесное представление предпочитаемых единиц измерения.
    '''

    user_preferences_instance = _get_user_preferences_instance()
    return user_preferences_instance.units_display


def set_units(units: str):
    '''
    Устанавливает значение полю units экземпляру настроек по словесному представлению предпочитаемых единиц измерения.

    Args:
        units (str): Словесное представление предпочитаемых единиц измерения.
        Одно из: Как на физике, Имперская, Метрическая.

    '''

    user_preferences_instance = _get_user_preferences_instance()
    user_preferences_instance.units = units
    user_preferences_instance.save()


def _get_user_preferences_instance() -> UserPreferences:
    '''
    Предоставляет экземпляр настроек пользователя.

    Returns:
        Экземпляр настроек пользователя.
    '''

    return UserPreferences.objects.all().first()
