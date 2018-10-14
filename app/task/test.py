from requests import Session
from bs4 import BeautifulSoup
from datetime import datetime
import pytz


s = Session()


r = s.get("http://news.buaa.edu.cn/xsjwhhd_new.htm")

soup = BeautifulSoup(r.content, "lxml")
articles = soup.find_all("div", class_="listleftop1")


def parseTime(t):
    return datetime.strptime(t + "+0800",
            "%Y-%m-%d%z").astimezone(pytz.utc)




for article in articles:
    url = article.find("a")
    time = article.find("em")
    timestamp = parseTime(time.string[1:-1])
    print(timestamp)
    print(url['href'], url.string, timestamp)


def get_detail(url: str):
    r = s.get(url)
    soup = BeautifulSoup(r.content, "lxml")
    main = soup.find("div", id="vsb_content")
    img = main.find("img")
    img_url = img['src'] if img else None
    count = 0
    print(img_url)
    segs = []
    for p in main.find_all("p"):
        t = p.get_text().strip()
        if t:
            segs.append(t)
            count += 1
            if count == 5:
                break
    print("\n".join(segs)[:200])




url = "http://news.buaa.edu.cn/" + articles[0].find("a")['href']

get_detail(url)

