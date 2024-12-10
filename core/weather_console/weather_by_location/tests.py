
if __name__ == '__main__':
    from .weather_by_location import get_latitude_and_longitude
    from weather_console.weather_api.openweathermap_api import get_weather_data
    coords = get_latitude_and_longitude()
    print(coords)
    data = get_weather_data(coords.get('lat'), coords.get('lon'))
    print(data)
