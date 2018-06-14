from threading import Timer
from pymongo import MongoClient
from selenium import webdriver
import time

class ResetCookiesForSpider(object):
    driver_list=[]
    def __init__(self, driver_num=0):
        self.client = MongoClient("mongodb://47.100.161.81:27017")
        db = self.client['cookies']
        self.table = db['weibo']
        for i in range(driver_num):
            driver = webdriver.Firefox()
            self.driver_list.append(driver)
            time.sleep(2)

    def set_cookies(self):
        for i in range(len(self.driver_list)):
            self.table.insert_one({'index':i, 'cookies':self.driver_list[i].get_cookies()})

    def reset_cookies(self):
        for i in range(len(self.driver_list)):
            self.driver_list[i].refresh()
            self.table.update_one({'index':i},{'$set':{'cookies':self.driver_list[i].get_cookies()}})

    def timer_cookies(self):
        self.reset_cookies()
        self.timer = Timer(1800, self.timer_cookies)
        self.timer.start()

    def close(self):
        self.client.close()
        try:
            self.timer.cancel()
        except Exception:
            print('timer cancel failed')
            pass
        for i in range(len(self.driver_list)):
            self.driver_list[i].close()


        
