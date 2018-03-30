import requests
import re

s = requests.Session()
s.headers
r = s.get('http://music.163.com/m/song?id=176053')
print(r.text)
# title = re.findall('<title>(.*?)</title>', r.text)[0]
# nickname = re.findall('<strong class="profile_nickname">(.*?)</strong>', r.text)[0]
# meta = re.findall('<span class="profile_meta_value">(.*?)</span>', r.text)[0]
# desc = re.findall('var msg_desc = "(.*?)";', r.text)[0]
# head_img = re.findall('var msg_cdn_url = "(.*?)";', r.text)[0]

# print(title)
# print(nickname)
# print(meta)
# print(desc)
# print(head_img)