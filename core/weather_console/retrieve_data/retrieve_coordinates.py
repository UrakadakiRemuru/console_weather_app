from typing import Dict, List

from rich.table import Table


def create_table_for_display_coordinate_refinement(geocoding_data: List[Dict[str, float | str | None]]) -> Table:
    '''
    Преобразует список словарей из преобразованных данных от geocoding в таблицу.
    Args:
        geocoding_data (List[Dict[str, float | str | None]]): Преобразованные данные от geocoding.

    Returns:
        Таблица для вывода.
    '''

    table = Table()
    table.add_column('Номер', justify='right')
    table.add_column('Город', justify='center')
    table.add_column('Область', justify='center')
    table.add_column('Страна', justify='center')

    for ind, city_obj in enumerate(geocoding_data):
        table.add_row(
            str(ind + 1),
            city_obj.get('city'),
            city_obj.get('state') or '',
            city_obj.get('country')
        )

    return table
