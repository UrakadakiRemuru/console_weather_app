import asyncio
import math
import os
from typing import Tuple, List

import keyboard
from django.db.models import QuerySet
from rich.console import Console
from rich.table import Table

from weather_console.models import UserRequestHistory


class Paginator:
    '''
    Класс для пагинации истории пользовательских запросов.
    '''

    def __init__(self, items: QuerySet[UserRequestHistory], page_size=5):
        self.items = items
        self.page_size = page_size
        self.total_pages = math.ceil(len(items) / page_size)
        self.current_page = 1

    def get_page_items(self) -> List[Tuple[str, str, str, bool]]:
        '''
        Предоставляет список элементов для отображения на одной странице.

        Returns:
            Список элементов.
        '''

        start = (self.current_page - 1) * self.page_size
        end = start + self.page_size
        return [(str(item.pk), item.city, item.country, item.is_current_location) for item in self.items[start:end]]

    def next_page(self):
        '''
        Повышает счетчик текущей страницы на 1, если это возможно.
        '''
        if self.current_page < self.total_pages:
            self.current_page += 1

    def prev_page(self):
        '''
        Понижает счетчик текущей страницы на 1, если это возможно.
        '''
        if self.current_page > 1:
            self.current_page -= 1

    def check_inserted_id(self, item_id: str):
        '''
        Валидирует введенный идентификационный номер на странице.

        Args:
            item_id (str): Введенный пользователем идентификационный номер.

        Raises:
              ValueError: В случае если пользователь ввел некорректный идентификационный номер.
        '''

        if not item_id.isdigit():
            raise ValueError('Значение должно быть целочисленным! '
                             'Пожалуйста, повторите запрос, используя корректные данные.')

        ids = [item[0] for item in self.get_page_items()]
        if item_id not in ids:
            raise ValueError(f'Введите одно из значений {ids}.')

        return int(item_id)

    def create_table_for_display_page(self) -> Table:
        '''
        Создает страницу с элементами для отображения.
        Returns:
            Таблица для отображения.
        '''

        table = Table(title=f'Страница {self.current_page}/{self.total_pages}')

        table.add_column('Номер', justify='left', style='bold')
        table.add_column('Название города', justify='center')
        table.add_column('Название страны', justify='center')
        table.add_column('Текущая локация', justify='center')

        for item_id, city_name, country_name, is_current_location in self.get_page_items():
            if is_current_location:
                table.add_row(item_id, '-', '-', 'Да')
            else:
                table.add_row(item_id, city_name, country_name, '-')

        return table

async def handle_arrows(paginator: Paginator, console: Console, stop_event: asyncio.Event):
    '''
    Обработчик нажатия стрелок.
    Args:
        paginator (Paginator): Экземпляр класса пагинации.
        console (Console): Экземпляр консоли.
        stop_event (asyncio.Event): Завершающее событие.

    '''

    while not stop_event.is_set():
        if keyboard.is_pressed("left"):
            paginator.prev_page()
            console.clear()
            console.print(paginator.create_table_for_display_page())
            console.print("Введите значение номера или просмотрите содержимое страниц,"
                          " используя стрелки на клавиатуре: \n")
            await asyncio.sleep(0.2)
        elif keyboard.is_pressed("right"):
            paginator.next_page()
            console.clear()
            console.print(paginator.create_table_for_display_page())
            console.print("Введите значение номера или просмотрите содержимое страниц,"
                          " используя стрелки на клавиатуре: \n")
            await asyncio.sleep(0.2)
        await asyncio.sleep(0.1)


async def get_request_id_from_user(paginator: Paginator, console: Console):
    stop_event = asyncio.Event()
    console.print(paginator.create_table_for_display_page())

    arrow_task = asyncio.create_task(handle_arrows(paginator, console, stop_event))

    try:
        while True:
            user_input = await asyncio.to_thread(
                console.input,
                "Введите значение номера или просмотрите содержимое страниц, используя стрелки на клавиатуре: \n",
            )
            try:
                return paginator.check_inserted_id(user_input)
            except ValueError as e:
                console.print(e.args[0])
    finally:
        stop_event.set()
        await arrow_task
