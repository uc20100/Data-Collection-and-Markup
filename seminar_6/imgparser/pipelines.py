# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import scrapy
# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from scrapy.pipelines.images import ImagesPipeline
import hashlib
from pymongo import MongoClient
import os


class ImgparserPipeline:
    """
    Класс ImgparserPipeline (Трубопровод), настраиваем БД, заносит данные в БД.

     Методы:
    -  process_item(self, item, spider): Функция заносит данные в БД MongoDB.

     Dunder методы:
    - __init__(self): конструктор класса.
    """

    def __init__(self):
        # Настраиваем клиент MongoDB (IP, порт)
        client = MongoClient('localhost', 27017)
        # Задаём название базы данных ('books')
        self.mongo_base = client.images

    def process_item(self, item, spider):
        """
        Функция записывает данные в БД MongoDB

        :param item: данные пришедшие из парсера
        :param spider:
        :return: запись в БД
        """

        # Создаём коллекцию в БД (имя нашего паука)
        collection = self.mongo_base[spider.name]
        try:
            # Добавляем запись в базу данных
            collection.insert_one(item)
        except ValueError:
            print('Ошибка добавления документа')
        return item


class PhotosPipeline(ImagesPipeline):
    """
    Класс PhotosPipeline (Трубопровод), записывает скаченный файл на диск.

     Атрибуты:
    - count_img: счётчик записанных файлов,

     Методы:
    - get_media_requests(self, item, info): Функция производит запись скаченного файла на диск, выводит информацию о количестве записей,
    - file_path(self, request, response=None, info=None, *, item=None): Функция назначает имя записываемому файла, задаёт id для записи в ПД MongoDB.
    """

    count_img = 0

    def get_media_requests(self, item, info):
        '''
        Функция производит запись скаченного файла на диск, выводит информацию о количестве записей.

        :param item:
        :param info:
        :return:
        '''
        try:
            # Выводим информацию о состоянии процесса
            self.count_img += 1
            print(f'Обработано {self.count_img} картинок')
            yield scrapy.Request(item['url'])
        except Exception as e:
            print(e)

    def file_path(self, request, response=None, info=None, *, item=None):
        '''
        Функция назначает имя записываемому файла, задаёт id для записи в ПД MongoDB.

        :param request:
        :param response:
        :param info:
        :param item:
        :return:
        '''
        image_guid = hashlib.sha1(request.url.encode()).hexdigest()
        file_name = f"{item['name']}-{image_guid}.jpg"
        # Записываем полный путь к файлу
        basedir = os.path.abspath(os.path.dirname(__file__))
        file_path = os.path.join(basedir + r'\images', file_name)
        item['path'] = f'{file_path}'
        # Записываем id
        item['_id'] = f'{image_guid}'
        return file_name
