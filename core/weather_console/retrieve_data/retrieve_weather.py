from datetime import datetime
from typing import Dict

from rich.table import Table

_HEADER_MAP = {
    'city': 'Город',
    'time': 'Текущее время',
    'weather': 'Погода',
    'temperature': 'Температура',
    'feels_like': 'Ощущается как',
    'wind_speed': 'Скорость ветра'
}


def create_table_for_display_weather(weather_data: Dict[str, str]) -> Table:
    '''
    Преобразует словарь из преобразованных данных от open weather в таблицу.
    Args:
        weather_data (Dict[str, str]): Преобразованные данные от open weather.

    Returns:
        Таблица для вывода.
    '''

    table = Table(show_header=False)
    table.add_column('Заголовки', justify='right', style='bold')
    table.add_column('Значения', justify='center')

    for weather_name, weather_value in weather_data.items():
        header = _HEADER_MAP.get(weather_name)
        table.add_row(
            header,
            str(weather_value)
        )

    # table.add_row('Текущее время', datetime.now().strftime('%H:%M:%S %d.%m.%Y'))

    return table
