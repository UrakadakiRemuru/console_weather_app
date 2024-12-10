from typing import Dict

from googletrans import Translator
from iso3166 import countries, countries_by_alpha2


def parse_user_input(input_string: str) -> Dict[str, str]:
    '''
    Парсинг введенных пользователем данных. Пользователь вводит либо название города, либо названия города и страны.
    Во втором случае данные должны быть разделены запятой.

    Args:
        input_string (str): Введенные пользователем данные.


    Returns:
        Словарь с названием города и страны или города.

    Examples:
        {
            'city': val,
            'country': val
        }

        {
            'city': val,
        }
    '''

    NAME_MAP = ('city', 'country')

    name_list: list[str] = input_string.replace(' ', '').split(',')

    return dict(zip(NAME_MAP, name_list))


def get_country_code(country_name: str, *, translator: Translator) -> str:
    '''
    Переводит название страны на английский и выдает код страны в формате ISO-3166.
    Args:
        country_name (str): Название страны на любом языке.
        translator (Translator): Экземпляр переводчика.

    Raises:
        ValueError: В случае если страна не была найдена.

    Returns:
        Код страны в формате ISO-3166.
    '''

    country_translation = translator.translate(country_name).text.capitalize()

    if country_translation == 'Russia':
        country_translation = 'Russian Federation'
    elif country_translation == 'England':
        country_translation = 'United Kingdom of Great Britain and Northern Ireland'

    try:
        country = countries.get(country_translation)
        return country.alpha2
    except LookupError as e:
        raise ValueError(f'Перепроверьте введенные данные {country_name} и повторите попытку.') from e


def get_translated_country_name_by_code(country_code: str, lang_preference: str = 'ru', *,
                                        translator: Translator) -> str:
    '''
    Получения названия страны на предпочитаемом языке из ISO-3166 кода.
    Args:
        country_code (str): ISO-3166 код страны.
        lang_preference (str): ISO-3166 код страны предпочитаемого языка.
        translator (Translator): Экземпляр переводчика.

    Raises:
        ValueError: В случае если страна не была найдена.

    Returns:
        Переведенное название страны.
    '''

    country_code = country_code.upper()
    lang_preference = lang_preference.lower()

    try:
        country = countries_by_alpha2.get(country_code)
        country_name = country.name
    except LookupError as e:
        raise ValueError(f'Перепроверьте введенные данные {country_code} и повторите попытку.') from e

    translated_country_name = translator.translate(country_name, dest=lang_preference).text
    translated_country_name = ' '.join([word.capitalize() for word in translated_country_name.split()])

    return translated_country_name


def translate_anything(string: str, lang_preference: str = 'ru', *, translator: Translator) -> str:
    '''
    Переводит заданную строку на предпочитаемый язык из ISO-3166 кода.
    Args:
        string (str): Строка, которую хотим перевести
        lang_preference (str): : ISO-3166 код страны предпочитаемого языка.
        translator (Translator): Экземпляр переводчика.

    Returns:
        Переведенная строка.
    '''

    lang_preference = lang_preference.lower()

    translated_string: str = translator.translate(string, dest=lang_preference).text

    return translated_string.capitalize()
