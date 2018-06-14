# -*- coding: utf-8 -*-
import scrapy
from scrapy import Request
from ..items import WeiboItem
from ..items import TweetsItem
from scrapy_splash import SplashRequest
from scrapy_redis.spiders import RedisSpider
from scrapy_redis.utils import bytes_to_str
import re
import time
import random
from pymongo import MongoClient 
from threading import Timer

#用与无需进行页面下啦操作的请求
lua_one='''
function main(splash)
    splash:init_cookies(splash.args.cookies)
    splash.images_enabled = false
    splash:set_user_agent('Mozilla/5.0 (iPad; CPU OS 5_0 like Mac OS X) AppleWebKit/534.46 (KHTML, like Gecko) Version/5.1 Mobile/9A334 Safari/7534.48.3')
    splash:go(splash.args.url)
    splash:wait(2)
    return splash:html()
end
'''
#用与需要进行下啦操作的请求
lua_two='''
function main(splash)
    splash:init_cookies(splash.args.cookies)
    splash.images_enabled = false
    splash:set_user_agent('Mozilla/5.0 (iPad; CPU OS 5_0 like Mac OS X) AppleWebKit/534.46 (KHTML, like Gecko) Version/5.1 Mobile/9A334 Safari/7534.48.3')
    splash:go(splash.args.url)
    splash:wait(1)
    splash:runjs("document.getElementsByClassName('WB_footer')[0].scrollIntoView(true)")
    splash:wait(2.5)
    splash:runjs("document.getElementsByClassName('WB_footer')[0].scrollIntoView(true)")
    splash:wait(2.5)
    return splash:html()
end
'''
class FansSpider(RedisSpider):
    name = 'fans'
    allowed_domains = ['weibo.com']
    begin_url = "https://weibo.com/p/1006051676082433/follow?relate=fans&from=100605&wvr=6&mod=headfans&current=fans#place"
    base_url = "http://weibo.com"
    parse_fans_times = 0
    parse_page_times = 0

    def __init__(self, *args, **kwargs):
        #在初始化中建立mongodb的链接，从数据库获取cookies
        self.client = MongoClient("mongodb://47.100.161.81:27017") 
        db = self.client['cookies']
        self.cookie_col = db.weibo
        self._reset_cookies()
        super(FansSpider, self).__init__(*args, **kwargs)

    def _reset_cookies(self):
        self.cookies = self.cookie_col.find_one({'index':4})['cookies']

    # def start_requests(self):
        # yield SplashRequest(self.begin_url, callback=self.parse_fans, dont_filter=True, cookies = self.cookies, endpoint='execute', args={'lua_source':lua_one}, cache_args=['lua_source'])

    def make_request_from_data(self, data):
        url = bytes_to_str(data, self.redis_encoding)
        return self.make_requests_from_url(url)

    #重写scrapy.Spider的这个方法，因为基于redis的分布式爬虫，start_urls由redis客户端输入，请求为默认的请求，需重写为splash请求才能切实爬取到start_urls
    def make_requests_from_url(self, url):
        return SplashRequest(url, callback=self.parse_fans, dont_filter=True, cookies = self.cookies, endpoint='execute', args={'lua_source':lua_one, 'images':0}, cache_args=['lua_source'])

    # def parse(self, response):
    #     yield SplashRequest(self.begin_url, callback=self.parse_fans, endpoint='execute', args={'lua_source':lua_one, 'images':0}, cache_args=['lua_source'])

    def parse_fans(self, response):
        #每跑1000次重置一次cookies,cookies从mongodb获取
        self.parse_fans_times = self.parse_fans_times+1
        if self.parse_fans_times % 1000 == 0:
            self._reset_cookies()
        #随机1-30sleep随机1-3
        r = random.randint(1,30)
        if r == 15:
            time.sleep(random.randint(1,3))
        li = response.css('div.follow_inner ul li.follow_item.S_line2')
        links = li.css('dt a::attr(href)').extract()
        for i in range(len(li)):
            weibo = WeiboItem()
            weibo['name'] = li[i].css('div.info_name a.S_txt1::text').extract_first()
            weibo['gender'] = li[i].css('div.info_name a i.W_icon::attr(class)').extract_first()
            weibo['location'] = li[i].css('div.info_add span::text').extract_first()
            info = li[i].css('div.info_connect a::text').extract()
            weibo['follows'] = info[0]
            weibo['fans'] = info[1]
            weibo['tweets'] = info[2]
            yield weibo
            hrefs = li[i].css('div.info_connect a::attr(href)').extract()
            #当粉丝数大于5时，下载该粉丝页面
            if int(info[1]) > 5:
                fans_url = '%s%s' % (self.base_url, hrefs[1])
                yield SplashRequest(fans_url, callback=self.parse_fans, cookies = self.cookies, endpoint='execute', args={'lua_source':lua_one, 'images':0}, cache_args=['lua_source'])
            #此处lua脚本并不完善，粗略的将执行方式分为两种，当博主微博总数小于20时无需执行js下啦动作即可获取微博，当大于20时，需要执行一次或两次的下啦动作才能获取页面内的微博
            if int(info[2]) < 20:
                tweets_url = '%s%s?is_all=1#_0' % (self.base_url, hrefs[2])
                yield SplashRequest(tweets_url, callback=self.parse_page, cookies = self.cookies, endpoint='execute', args={'lua_source':lua_one, 'images':0}, cache_args=['lua_source'])
            if int(info[2]) >= 20:
                tweets_url = '%s%s?is_all=1#_0' % (self.base_url, hrefs[2])
                yield SplashRequest(tweets_url, callback=self.parse_page, cookies = self.cookies, endpoint='execute', args={'lua_source':lua_two, 'images':0}, cache_args=['lua_source'])        
        next_page = response.css('div.W_pages a:last-child::attr(href)').extract_first()
        if next_page is not None:
            cur_page = re.findall(r'page=(\d)#', next_page)[0]
            #微博只能查看粉丝前五页
            if int(cur_page) < 6 :
                page_url = '%s%s' % (self.base_url, next_page)
                yield SplashRequest(page_url, callback=self.parse_fans, cookies = self.cookies, endpoint='execute', args={'lua_source':lua_one, 'images':0}, cache_args=['lua_source'])


    # 从高圆圆主页点击粉丝，页面由parse_fans来解析各个粉丝的链接，在从各个粉丝的主页点击他们的粉丝，再解析
    def parse_page(self, response):
        #每跑1000次重置一次
        self.parse_page_times = self.parse_page_times+1
        if self.parse_page_times % 700 == 0:
            self._reset_cookies()
        r = random.randint(1,30)
        if r == 15:
            time.sleep(random.randint(1,3))
        href = response.css('table.tb_counter td.S_line1 a.t_link.S_txt1::attr(href)').extract_first()
        url = 'http:%s' % href
        tweets = response.css('div.WB_cardwrap.WB_feed_type.S_bg2.WB_feed_like')
        for i in range(len(tweets)):
            tweet = TweetsItem()
            tweet['name'] = tweets[i].css('div.WB_detail div.WB_info a::text').extract_first()
            content = tweets[i].css('div.WB_text.W_f14::text').extract()
            tweet['content'] = ','.join(content).strip()
            handle = tweets[i].css('div.WB_handle span em::text').extract()
            tweet['like'] = handle[-1]
            tweet['comment'] = handle[-3]
            tweet['transfer'] = handle[3]
            tweet['tools'] = tweets[0].css('div.WB_from.S_txt2 a::text').extract()[1]
            yield tweet
        #如果有多页微博，则递归爬取
        next_page = response.css('div.W_pages a.page.next::attr(href)').extract_first()        
        if next_page is not None:
            next_url = '%s%s' % (self.base_url, next_page)
            yield SplashRequest(next_url, callback=self.parse_page, cookies = self.cookies, endpoint='execute', args={'lua_source':lua_two, 'images':0}, cache_args=['lua_source'])




