"""
Задание:
1.	Ознакомиться с некоторые интересными API. https://docs.ozon.ru/api/seller/
https://developers.google.com/youtube/v3/getting-started https://spoonacular.com/food-api
2.	Потренируйтесь делать запросы к API. Выберите публичный API, который вас интересует, и потренируйтесь
делать API-запросы с помощью Postman. Поэкспериментируйте с различными типами запросов и попробуйте получить
различные типы данных.
3.	Сценарий Foursquare
4.	Напишите сценарий на языке Python, который предложит пользователю ввести интересующую его категорию
(например, кофейни, музеи, парки и т.д.).
5.	Используйте API Foursquare для поиска заведений в указанной категории.
6.	Получите название заведения, его адрес и рейтинг для каждого из них.
7.	Скрипт должен вывести название и адрес и рейтинг каждого заведения в консоль.
"""

import os
import requests
from dotenv import load_dotenv
from functools import wraps
from typing import Callable
import logging
from pprint import pprint

__all__ = ['log_file']


LATITUDE_MIN = -90      # Широта минимум
LATITUDE_MAX = 90       # Широта максимум
LONGITUDE_MIN = -180    # Долгота минимум
LONGITUDE_MAX = 180     # Долгота максимум
RADIUS_MIN = 50         # Радиус минимум (метры)
RADIUS_MAX = 100_000    # Радиус максимум (метры)


# Настраиваем логирование
logging.basicConfig(format='{levelname:<8} - {asctime}. {msg}',
                    style='{',
                    filename='log_info.log',
                    filemode='a',
                    encoding='utf-8',
                    level=logging.INFO,
                    datefmt='%Y-%m-%d %H:%M:%S')
# Задаём переменную логирования
logger_val = logging.getLogger(__name__)


class UsException(BaseException):
    pass


# Создаем свой класс исключений
class ValueException(UsException):
    """
        Класс ошибки значений переменных.

         Атрибуты:
        - self.min_value (float): минимальное значение переменной,
        - self.max_value (float): максимальное значение переменной,
        - self.param_name (str): название переменной,
        - self.value (float): значение переменной.

         Dunder методы:
        - __init__(self, self_out, value): конструктор класса,
        - __str__(self): Возвращает строковое представление ошибки.
        """

    def __init__(self, self_out, value):
        self.min_value = self_out.min_value
        self.max_value = self_out.max_value
        self.param_name = self_out.param_name[1:]
        self.value = value

    def __str__(self):
        if self.value is not None:
            return (f"Для переменной '{self.param_name}' не соблюдается условие:"
                    f" {self.min_value} <= {self.value} <= {self.max_value}")
        else:
            return f"Не задано значение переменной '{self.param_name}' = {self.value}"


def log_file(logger: logging.Logger):
    """
    Функция логирования работы (Декоратор).

    :param logger: переменная логирования.
    :return:
    """

    def info_func(func: Callable):
        """
        Функция декоратор.

        :param func: Декорируемая функция
        :return:
        """

        @wraps(func)
        def write_log(*args, **kwargs):
            """
            Функция записи log файла.

            :param args: Позиционные аргументы,
            :param kwargs: ключевые аргументы,
            :return: результат работы функции.
            """
            try:
                result_value = func(*args, **kwargs)
                if func.__name__ == 'get_info':
                    # Логируем инфу
                    logger.info(result_value)
                return result_value
            except ValueException as e:
                mes = f'Функция "{func.__name__}().", {e}'
                # Логируем ошибку
                logger.error(mes)

        return write_log

    return info_func


class Value:
    """
    Дескриптор класса FoursquareParser.

     Атрибуты:
    - self.min_value (float): минимальное значение переменной,
    - self.max_value (float): максимальное значение переменной,

     Методы:
    - validate(value, param): выполняет валидацию переменной.

     Dunder методы:
    - __init__(self, min_value: int = None, max_value: int = None): конструктор класса,
    - __set_name__(self, owner, name): вызывается при создании атрибута класса,
    - __set__(self, instance, value): выполняет действие при задании значения атрибуту класса,
    - __get__(self, instance, owner): выполняет действие при обращении к атрибуту класса.
    """

    def __init__(self, min_value: float = None, max_value: float = None):
        self.min_value = min_value
        self.max_value = max_value

    def __set_name__(self, owner, name):
        """
        Функция создает новое имя переменной.

        :param owner:
        :param name:
        :return:
        """
        self.param_name = '_' + name

    def __get__(self, instance, owner):
        """
        Функция возвращает значение заданной переменной.

        :param instance:
        :param owner:
        :return: значение заданной переменной.
        """
        return getattr(instance, self.param_name)

    @log_file(logger_val)
    def __set__(self, instance, value):
        """
        Функция валидирует и задает значение переменных (пишет лог. если произошла ошибка валидации).

        :param instance:
        :param value: значение переменной.
        :return:
        """
        self.validate(self, value)
        setattr(instance, self.param_name, value)

    @staticmethod
    def validate(self, value):
        """
        Функция валидирует значения атрибута.

        :param self: self значения переменной,
        :param value: значение переменной,
        :return: вызывает ошибку если со значениями, что-то не так.
        """
        if (self.min_value is not None and self.max_value is not None) and isinstance(value, float):
            if not (self.min_value <= value <= self.max_value):
                raise ValueException(self, value)
        else:
            if value is None:
                raise ValueException(self, value)


class FoursquareParser:
    """
    Класс 'API сервиса Foursquare'

     Атрибуты:
    - __api_key (str): ключ API выданный на сервисе Foursquare,
    - latitude (float): широта центра окружности,
    - longitude (float): долгота центра окружности,
    - radius (float): радиус окружности поиска,
    - query (str): что нужно найти.

     Методы:
    - get_info(self, query=None, latitude=None, longitude=None, radius=None) -> str: выводит информацию по нашему запросу.

     Dunder методы:
    - __init__(self, api_key): Конструктор класса,
    - __str__(self): Возвращает строковое представление студента, включая имя и список предметов.
    """

    # Чтение и запись в этих переменных будет производиться в дискрипторе (class Value)
    __api_key = Value()
    latitude = Value(LATITUDE_MIN, LATITUDE_MAX)
    longitude = Value(LONGITUDE_MIN, LONGITUDE_MAX)
    radius = Value(RADIUS_MIN, RADIUS_MAX)
    query = Value()

    def __init__(self, api_key: str = ''):
        self.__api_key = api_key

    def __str__(self):
        """
        Функция возвращает строковое представление студента, включая имя и список предметов.

        :return:
        """
        pass

    @log_file(logger_val)
    def get_info(self, query=None, latitude=None, longitude=None, radius=None):
        """
        Функция выводит информацию по запросу.

        :param query: запрос (кофейня, магазин и т.д.),
        :param latitude: широта центра окружности,
        :param longitude: долгота центра окружности,
        :param radius: радиус окружности,
        :return: ответ в текстовом формате (Название, адрес, рейтинг, страна)
        """

        # Если значение переменных изменилось - обновляем значение
        if query is not None:
            self.query = query
        if latitude is not None:
            self.latitude = latitude
        if longitude is not None:
            self.longitude = longitude
        if radius is not None:
            self.radius = radius

        # Адрес API
        url = 'https://api.foursquare.com/v3/places/search'
        # Параметры запроса API
        params = {
            'll': f'{self.latitude},{self.longitude}',
            'radius': self.radius,
            'query': self.query,
            'fields': 'name,location,rating',
        }
        # Заголовок запроса
        headers = {
            'Authorization': self.__api_key,
            'accept': 'application/json',
        }

        # Выполняем API запрос
        response = requests.get(url=url, params=params, headers=headers)
        # Преобразуем текст в словарь
        j_data = response.json()

        # Формируем текстовый ответ
        res = f'Широта: {self.latitude}, Долгота: {self.longitude}, Радиус {self.radius:_} м., Запрос: "{self.query}" \n'
        for item in j_data.get('results'):
            list_str = [f'Название: {item.get('name')}', f'Страна:   {item.get('location').get('country')}',
                        f'Адрес:    {item.get('location').get('formatted_address')}', f'Рейтинг:  {item.get('rating')}']
            longest = len(max(list_str, key=len))
            list_str.append(f'{'-' * longest}\n')
            res += '\n'.join(list_str)

        return res


if __name__ == '__main__':

    # Загружаем API ключ из окружения
    dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path)

    foursquare_api_key = os.getenv('API_KEY')
    parser_obj = FoursquareParser(api_key=foursquare_api_key)
    # Выводим мнфу на консоль и в лог. файл, также лог. файл пишутся и исключения ValueException
    print(parser_obj.get_info(query='кофе', latitude=53.479782, longitude=49.484156, radius=5_000))
    print(parser_obj.get_info(query='парикмахерская'))


