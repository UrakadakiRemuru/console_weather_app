from typing import Dict

from geocoder import ipinfo

def get_latitude_and_longitude() -> Dict[str, float]:
    '''
    Получение широты и долготы по данным IP-адреса текущего местоположения.

    Raises:
        ConnectionError: В случае проблем с соединением или проблем на стороне сервиса.

    Returns:
        Словарь, содержащий широту и долготу.

    Examples:
         {
            'lat': ...,
            'lon': ...,
         }
    '''
    names = ('lat', 'lon')
    try:
        response = ipinfo('me')
    except ConnectionError as e:
        raise ConnectionError('Проверьте подключение к интернету и повторите попытку.') from e

    if response.status_code == 200:
        return dict(zip(names, response.latlng))

    raise ConnectionError('Возникли проблемы на стороне сервиса. Повторите попытку позже.')
