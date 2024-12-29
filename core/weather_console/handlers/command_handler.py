import asyncio
import os
from typing import List, Dict

import django
from django.db import transaction
from googletrans import Translator
from rich.console import Console

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from weather_console.handlers.paginator import Paginator, get_request_id_from_user
from weather_console.retrieve_data.retrieve_coordinates import create_table_for_display_coordinate_refinement
from weather_console.retrieve_data.retrieve_weather import create_table_for_display_weather
from weather_console.services.model_services import (
    fill_db, get_user_request_history, get_request_instance_by_user_request,
    get_user_request_instance, increase_user_request_counter, get_weather_instance_by_user_request, get_is_first_time,
    set_is_first_time, get_instruction_on_start, set_instruction_on_start, get_language_code, get_language,
    set_language, get_units_code, get_units, set_units
)
from weather_console.services.prepare_data import prepare_request_data, prepare_response_data
from weather_console.utilities.utils import prepare_weather_data_to_representation
from weather_console.weather_api.geocoding_api import (
    get_city_coordinates, parse_geocoding_response, get_coordinates_from_parsed_geocoding_response,
    get_city_coordinates_reversed
)
from weather_console.weather_api.openweathermap_api import get_weather_data, parse_weather_data
from weather_console.weather_by_location.weather_by_location import get_latitude_and_longitude
from weather_console.weather_by_name.weather_by_name import get_location_names


class CommandHandler:
    '''
    Обработчик консольных команд.
    '''

    def __init__(self):
        self._COMMAND_MAP = {
            r'\вгороде': self._handle_weather_by_name,
            r'\влокации': self._handle_weather_by_location,
            r'\впопулярные': self._handle_request_history,
            r'\внастройки': self._handle_settings,
            r'\винструкцию': self._show_instructions,
            r'\выйти': self._exit,
        }
        self._translator = Translator()
        self._console = Console()
        self._is_running = True
        self._HISTORY_CHOICE_MAP = {
            'r': self._repeat_request,
            'h': self._show_weather_from_history
        }

    @property
    def _is_first_time(self):
        return get_is_first_time()

    @_is_first_time.setter
    def _is_first_time(self, marker: bool):
        set_is_first_time(marker)

    @property
    def _instruction_on_start(self):
        return get_instruction_on_start()

    @_instruction_on_start.setter
    def _instruction_on_start(self, marker: bool):
        set_instruction_on_start(marker)

    @property
    def _language_code(self):
        return get_language_code()

    @property
    def _language(self):
        return get_language()

    @_language.setter
    def _language(self, lang: str):
        set_language(lang)

    @property
    def _units_code(self):
        return get_units_code()

    @property
    def _units(self):
        return get_units()

    @_units.setter
    def _units(self, units: str):
        set_units(units)

    def _handle_weather_by_name(self):
        '''
        Обработка команды \вгороде.
        '''

        user_input = self._console.input('Введите название города, в котором хотите узнать погоду.'
                                         'Вы также можете уточнить страну расположение города, '
                                         'это повысит точность результата. \n'
                                         'Формат ввода {город} или {город, страна}: ')

        try:
            city_country_data = get_location_names(user_input, translator=self._translator)
        except ValueError as e:
            self._console.print(e.args[0])
            return self._handle_weather_by_name()

        try:
            coordinates_geocoding = get_city_coordinates(city_country_data)
        except (ConnectionError, TimeoutError, ValueError) as e:
            self._console.print(e.args[0])
            return

        coordinates_list = parse_geocoding_response(
            coordinates_geocoding,
            self._language_code,
            translator=self._translator)

        city_coordinates = self._refinement_city(coordinates_list)

        try:
            parsed_weather_data = self._get_parsed_weather_data(city_coordinates)
        except (ConnectionError, TimeoutError) as e:
            self._console.print(e.args[0])
            return

        fill_db(city_coordinates, parsed_weather_data)
        self._to_representation_weather(city_coordinates, parsed_weather_data)

    def _get_refinement_index_of_city(self, city_amount: int):
        '''
        Уточняет координаты города, в случае множественного ответа от geocoding.

        Args:
            city_amount (int): Количество городов в ответе от geocdoing.

        Returns:
            Индекс для получения нужного города в промежутке от 0 до city_amount - 1.
        '''

        try:
            val = int(self._console.input())
            if val < 1:
                raise ValueError
            return val - 1
        except ValueError:
            self._console.print(f'Необходимо ввести целочисленное значение от 1 до {city_amount}. \n')
            return self._get_refinement_index_of_city(city_amount)

    def _refinement_city(self, parsed_geocoding_response: List[Dict[str, float | str | None]]) -> Dict[
        str,
        float | str | None
    ]:
        '''
        Уточняет город при множественном выборе городов и возвращает словарь выбранного пользователем
        города.

        Args:
            parsed_geocoding_response (List[Dict[str, float | str | None]]): Отформатированный ответ от geocoding.

        Returns:
            Выбранный город.
        '''

        city_amount = len(parsed_geocoding_response)

        if city_amount != 1:
            table_coordinates = create_table_for_display_coordinate_refinement(parsed_geocoding_response)
            self._console.print('Выберите номер нужного вам города: ', table_coordinates)
            city_index = self._get_refinement_index_of_city(city_amount)
            return parsed_geocoding_response[city_index]

        return parsed_geocoding_response[0]

    def _get_parsed_weather_data(self, city_coordinates: Dict[str, float | str | None]) -> Dict[
        str,
        str | float | int]:
        '''
        Предоставляет отформатированные данные о погоде, исходя из координат города.

        Args:
            city_coordinates (Dict[str, float | str | None]): Данные о городе.

        Raises:
            ConnectionError: В случае если присутствуют проблемы с интернет-соединением.

        Returns:
            Данные о погоде.
        '''

        coords = get_coordinates_from_parsed_geocoding_response(city_coordinates)
        weather_data = get_weather_data(*coords, units=self._units_code, lang_preference=self._language_code)
        return parse_weather_data(weather_data)

    def _to_representation_weather(self,
                                   city_coordinates: Dict[str, float | str | None],
                                   parsed_weather_data: Dict[str, str | float | int]
                                   ):
        '''
        Выводит в консоль прогноз погоды.

        Args:
            city_coordinates (Dict[str, float | str | None]): Данные о городе.
            parsed_weather_data (Dict[str, str | float | int]): Данные о погоде.

        '''

        parsed_weather_data = prepare_weather_data_to_representation(parsed_weather_data, city_coordinates,
                                                                     self._units_code)
        weather_table = create_table_for_display_weather(parsed_weather_data)
        self._console.print(weather_table)

    def _handle_weather_by_location(self):
        '''
        Обработка команды \влокации.
        '''

        try:
            coords = get_latitude_and_longitude()
        except ConnectionError as e:
            self._console.print(e.args[0])
            return

        try:
            coordinates_geocoding = get_city_coordinates_reversed(**coords)
        except (ConnectionError, TimeoutError, ValueError) as e:
            self._console.print(e.args[0])
            return

        coordinates_list = parse_geocoding_response(
            coordinates_geocoding,
            self._language_code,
            translator=self._translator)

        city_coordinates = self._refinement_city(coordinates_list)

        try:
            parsed_weather_data = self._get_parsed_weather_data(city_coordinates)
        except (ConnectionError, TimeoutError) as e:
            self._console.print(e.args[0])
            return

        fill_db(city_coordinates, parsed_weather_data, is_current_location=True)
        self._to_representation_weather(city_coordinates, parsed_weather_data)

    def _handle_request_history(self):
        '''
        Обработка команды \впопулярные.
        '''

        user_request_history = get_user_request_history()
        paginator = Paginator(user_request_history)
        user_request_pk = asyncio.run(get_request_id_from_user(paginator, self._console))
        user_choice = self._refinement_choice()
        self._HISTORY_CHOICE_MAP.get(user_choice)(user_request_pk)

    def _refinement_choice(self) -> str:
        '''
        Уточняет действие пользователя.

        Returns:
            r - в случае если пользователь желает повторить запрос, h - если пользователь желает посмотреть данные из
            истории.
        '''

        user_choice = self._console.input('Если вы хотите повторить запрос отправьте R, если вы хотите посмотреть'
                                          ' данные о погоде из прошлого запроса отправьте H: ').lower()
        if user_choice in {'r', 'h'}:
            return user_choice

        self._console.print(f'Вы ввели некорректные данные {user_choice}. \n')
        return self._refinement_choice()

    def _repeat_request(self, user_request_pk: int):
        user_request = get_user_request_instance(user_request_pk)
        request = get_request_instance_by_user_request(user_request_pk)
        coords = prepare_request_data(request)

        try:
            coordinates_geocoding = get_city_coordinates_reversed(**coords)
        except (ConnectionError, TimeoutError, ValueError) as e:
            self._console.print(e.args[0])
            return

        coordinates_list = parse_geocoding_response(
            coordinates_geocoding,
            self._language_code,
            translator=self._translator)

        city_coordinates = self._refinement_city(coordinates_list)

        try:
            parsed_weather_data = self._get_parsed_weather_data(city_coordinates)
        except (ConnectionError, TimeoutError) as e:
            self._console.print(e.args[0])
            return

        increase_user_request_counter(user_request)
        self._to_representation_weather(city_coordinates, parsed_weather_data)

    def _show_weather_from_history(self, user_request_pk: int):
        user_request = get_user_request_instance(user_request_pk)
        response = get_weather_instance_by_user_request(user_request_pk)
        parsed_weather_data = prepare_response_data(user_request, response, self._units_code)
        weather_table = create_table_for_display_weather(parsed_weather_data)
        self._console.print(weather_table)

    def _handle_settings(self):
        '''
        Обработка команды \внастройки.
        '''

        with transaction.atomic():
            self._process_language()
            self._process_units()
            self._process_instruction()

    def _process_language(self):
        '''Настройка данных языка.'''

        lang = self._console.input('Выберите предпочитаемый язык (русский, английский, испанский): ')
        try:
            self._language = lang.lower()
        except ValueError as e:
            self._console.print(e.args[0], f'Проверьте введенные данные {lang} и повторите снова. \n')
            return self._process_language()

    def _process_units(self):
        '''Настройка данных единиц измерения.'''
        units = self._console.input('Выберите предпочитаемые единицы измерения '
                                    '(Как на физике, Метрическая, Имперская): ')
        try:
            self._units = units.lower()
        except ValueError as e:
            self._console.print(e.args[0], f'\n Проверьте введенные данные {units} и повторите снова. \n')
            return self._process_units()

    def _process_instruction(self):
        '''Настройка инструкций при запуске.'''
        choice = self._console.input('Необходимо ли показывать инструкцию при каждом запуске? (Y/N): ').lower()
        CHOICE_MAP = {
            'y': True,
            'n': False
        }

        if choice not in CHOICE_MAP:
            self._console.print('Введите корректные данные "Y" или "N". \n')
            return self._process_instruction()

        self._instruction_on_start = CHOICE_MAP.get(choice)

    def _show_instructions(self):
        '''Демонстрация инструкции.'''

        instruction = '''Для использования приложения необходимо подключение к интернету.
Иногда приложение будет запрашивать ввод букв, для подтверждения или уточнения действий. Пожалуйста, используйте 
буквы латинского алфавита.
Чтобы узнать погодные условия в городе, воспользуйтесь командой \вгороде и следуйте дальнейшим указаниям. 
Для получения информации о погоде по вашему текущему месторасположению, используйте команду \влокации.
Чтобы посмотреть историю ваших запросов введите \впопулярные. Данная команда позволят как повторить выбранный 
запрос, так и показать погодные условия, полученные в результате вашего последнего запроса.
Для настройки используйте команду \внастройки и следуйте инструкциям.
Для повторного отображения настроек введите команду \винструкцию.
Для выхода из приложения напишите \выйти.
'''
        self._console.print(instruction)

    def _help(self):
        '''Демонстрирует краткую инструкцию.'''

        commands = '''
1. \вгороде - узнать погоду по названию города. \n
2. \влокации - узнать погоду в текущей локации. \n
3. \впопулярные - просмотреть список самых популярных запросов. \n
4. \внастройки - настройки персонализации. \n
5. \винструкцию - показать инструкцию использования. \n
6. \выйти - выход из приложения. \n
        '''
        self._console.print(commands)


    def _exit(self):
        '''
        Обработка команды \выход.
        '''

        self._is_running = False
        self._console.print('Спасибо, что воспользовались приложением! Всего доброго!')

    def run(self):
        '''
        Запуск обработчика консольных команд.
        '''
        self._console.print('Здравствуйте! \n')
        if self._is_first_time or self._instruction_on_start:
            if self._is_first_time:
                self._console.print('Далее вам будем предложено осуществить настройку приложения. \n')
                self._handle_settings()
                self._is_first_time = False
            self._help()

        self._start()

    def _start(self):
        while self._is_running:
            try:
                command = self._console.input('Введите команду: ')
                if not command.startswith('\\'):
                    self._console.print(f'Введенной команды {command} не существует! Введите одну из '
                                        f'списка \вгороде, \влокации, \впопулярные, \внастройки, \выйти. \n')
                else:
                    handler = self._COMMAND_MAP.get(command)
                    if not handler:
                        self._console.print(f'Введенной команды {command} не существует! Введите одну из '
                                            f'списка \вгороде, \влокации, \впопулярные, \внастройки, \выйти. \n')
                        self._start()
                    else:
                        handler()
            except KeyboardInterrupt:
                self._exit()
