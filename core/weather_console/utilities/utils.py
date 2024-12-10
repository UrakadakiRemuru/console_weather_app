from googletrans import Translator


def get_translator() -> Translator:
    '''
    Получение экземпляра переводчика.

    Raises:
        ConnectionError: В случае если возникли проблемы с подключением к сервису переводчика.

    Returns:
        экземпляр переводчика.
    '''
    try:
        return Translator()
    except ConnectionError as e:
        raise ConnectionError('Произошла ошибка подключения к сервису.'
                              ' Проверьте подключение к интернету и повторите попытку позже.') from e
