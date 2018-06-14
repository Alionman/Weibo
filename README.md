# Weibo
实现微博PC版爬虫

工具：
  Mac,3台阿里云服务器+1台华为云服务器

软件：\n
  scrapy爬虫框架，docker的splash引擎，缓存redis，数据库mongodb，抓包charles，selenium+firefox/chrome获取cookies及模拟刷新等操作

实现方式：
  scrapy本身不支持分布式爬虫，但是可以结合redis来实现，scrapy_redis重写了scrapy的Scheduler类;页面js加载由splash实现；

去重策略：
  因为我的服务器内存有限，我改写了scrapy_redis的dupefilter，使用了bloomfilter来去重，主要是改写request_seen方法，bloomfilter采取哈希函数位映射的方式去重(存在一定误判),redis支持setbit的写入方式，开辟一块256M的内存大概能区分9千万条request。

验证策略：
  我把获取cookies代码写了两个类ResetCookiesForSpider，一个是chrome的driver，一个时firefox的driver；使用自动化测试工具selenium来打开页面，手动登录微博(最好是有多个微博账号，这样可以经常切换cookies，避免被ban),调用自实现的方法timer_cookies可以定时模拟刷新页面再获取cookies

服务器的配置：
  起redis的服务端，以及mongodb的服务端；配置文件可自行百度；同时设置了开机自启；安装docker，pull splash，设置restart=always,同时设置开机自启；

内存问题：
  splash比较吃内存，我的云服务器内存较小，我采取的策略是起个crontab任务，定时跑脚本获取当前内存使用情况，如果达到警告值则自动重启docker，并输出内存使用值及重启时间点到日志中;重启docker内释放splash吃的内存，在非宕机下大概需要1-3秒，我设置了retry-times=5此间的request会重试，避免了因docker重启导致的request丢失问题；

服务器测试： 
  写了个脚步（test_splash_server.py）测试当前部署的splash服务器是否可达，访问配置了负载均衡nginx的服务器，请求轮训到各台服务器的splash进程

服务器管理工具：
  之前一直是通过终端命令进行管理和操作，最近发现了一款服务器集群管理的面板appnode；爬虫期间的各台服务器cpu及内存使用情况都能直观看到
