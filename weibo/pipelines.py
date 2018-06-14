# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html

from .items import WeiboItem, TweetsItem
import pymongo
from twisted.internet.threads import deferToThread
from scrapy.exceptions import DropItem

class WeiboPipeline(object):
    def process_item(self, item, spider):
        return item

#item去重以及去除无效项 
class DuplicatesPipeline(object):
    def __init__(self):
        #此处可以考虑将set本地存储化
        self.weibo_set = set()
        self.tweet_set = set()

    def process_item(self, item, spider):
        return deferToThread(self._process_item, item, spider)

    def _process_item(self, item, spider):
        if isinstance(item, WeiboItem):
            name = item['name']
            if name in self.weibo_set:
                raise DropItem("Duplicate weibo found: %s" % item)
        elif isinstance(item, TweetsItem):
            content = item['content']
            if content in self.tweet_set:
                raise DropItem("Duplicate tweet found: %s" % item)         
        return item



        title = item['title']
        if title in self.title_set:   #去除重复项
            raise DropItem("Duplicate title found: %s" % item)
        if title == None or title == "":    #去除空项
            raise DropItem("Invalid item found: %s" % item)
        self.title_set.add(title)
        return item

#将数据存入MongoDB
class MongoDBPipeline(object):
    @classmethod
    def from_crawler(cls, crawler):
        #从setting文件获取mongodb服务器以及数据库名，如果没有设置则使用默认项
        cls.DB_URI = crawler.settings.get('MONGO_DB_URI', 'mongodb://localhost:27017/')
        cls.DB_NAME = crawler.settings.get('MONGO_DB_NAME', 'weibo')
        return cls()

    def open_spider(self, spider):
        self.client = pymongo.MongoClient(self.DB_URI)
        self.db = self.client[self.DB_NAME]

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        #使用了twisted的多线程，能实现异步IO
        return deferToThread(self._process_item, item, spider)

    def _process_item(self, item, spider):
        ''' 判断item的类型，再入数据库 '''
        if isinstance(item, WeiboItem):
            try:
                self.db['weibos'].insert_one(dict(item))
            except Exception:
                pass
        elif isinstance(item, TweetsItem):
            try:
                self.db['tweets'].insert_one(dict(item))
            except Exception:
                pass                
        return item