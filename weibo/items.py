# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class WeiboItem(scrapy.Item):
    # define the fields for your item here like:
    name = scrapy.Field()
    gender = scrapy.Field()   
    location = scrapy.Field()
    fans = scrapy.Field()
    follows = scrapy.Field()
    tweets = scrapy.Field()

class TweetsItem(scrapy.Item):
    name = scrapy.Field()
    content = scrapy.Field()
    like = scrapy.Field()
    comment = scrapy.Field()
    transfer = scrapy.Field()
    tools = scrapy.Field()
