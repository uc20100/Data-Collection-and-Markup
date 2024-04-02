# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy
from itemloaders.processors import TakeFirst, MapCompose, Compose

def process_name(value):
    '''
    Функция ничего не делает, оставил для примера, чтобы не забыть.

    :param value:
    :return:
    '''
    return value


class ImgparserItem(scrapy.Item):
    """
    Класс упаковки данных.

     Атрибуты:
    - name: название картинки,
    - path: локальный адрес,
    - category: категория картинки,
    - url: адрес картинки в internet,
    - _id: id записи.
    """
    # define the fields for your item here like:
    name = scrapy.Field(input_processor=Compose(process_name), output_processor=TakeFirst())
    path = scrapy.Field()
    category = scrapy.Field(output_processor=TakeFirst())
    url = scrapy.Field(output_processor=TakeFirst())
    _id = scrapy.Field()

