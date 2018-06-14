import requests
from urllib.parse import quote
import re

def testSplash():
    lua = '''
    function main(splash, args)
      local treat = require("treat")
      local response = splash:http_get("http://httpbin.org/get")
      return treat.as_string(response.body)
    end
    '''
    #此url是配置了负载均衡的nginx进程，能讲请求轮训到各台服务器的splash进程
    url = 'http://:80/execute?lua_source=' + quote(lua)
    response = requests.get(url)
    ip = re.search('(\d+\.\d+\.\d+\.\d+)', response.text).group(1)
    return ip

if __name__ == "__main__":
    ips = []
    ip = testSplash()
    while ip not in ips:
        ips.append(ip)
        print(ip)
        ip = testSplash()
