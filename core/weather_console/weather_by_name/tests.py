if __name__ == '__main__':
    from weather_console.weather_by_name.weather_by_name import parse_user_input, get_country_code, \
        get_translated_country_name_by_code
    from weather_console.utilities.utils import get_translator

    translator = get_translator()

    assert parse_user_input('Moscow, Russia') == {'city': 'Moscow', 'country': 'Russia'}
    assert parse_user_input('London') == {'city': 'London'}
    assert parse_user_input('asdf,asdf,asdf,asdf') == {'city': 'asdf', 'country': 'asdf'}

    assert get_country_code('англия', translator=translator) == 'GB'
    assert get_country_code('россия', translator=translator) == 'RU'

    print(get_translated_country_name_by_code('ru', 'ru', translator=translator))
