from setup import setup_django
from weather_console.handlers.command_handler import CommandHandler
def main():
    '''Запуск.'''
    command_handler = CommandHandler()
    command_handler.run()


if __name__ == "__main__":
    setup_django()

    main()
