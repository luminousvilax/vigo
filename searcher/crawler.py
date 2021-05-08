import os

import pytz
import socket
import time
import urllib.parse
import urllib.request
from datetime import timedelta, date
import django
from bs4 import BeautifulSoup
from django.utils import dateparse
import logging
from searcher.models import News
from django.db.models import ObjectDoesNotExist

logger = logging.getLogger('vigo')
user_agent = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64)'
headers = {'User-Agent': user_agent}

keyword = '编辑'

def get_one_page_news(page_url):
    root = 'http://www.chinanews.com'
    req = urllib.request.Request(page_url, headers=headers)

    try:
        response = urllib.request.urlopen(req, timeout=10)
        html = response.read()
    except socket.timeout as err:
        logger.debug('socket.timeout')
        logger.debug(err)
        return []
    except Exception as e:
        logger.debug("-----%s:%s %s-----" % (type(e), e, page_url))
        return []

    soup = BeautifulSoup(html, "html.parser")

    news_pool = []
    news_list = soup.find('div', class_="content_list")
    items = news_list.find_all('li')
    for i, item in enumerate(items):

        if len(item) == 0:
            continue

        a = item.find('div', class_="dd_bt").find('a')
        title = a.string
        url = a.get('href')
        if root in url:
            url = url[len(root):]

        category = ''
        try:
            category = item.find('div', class_="dd_lm").find('a').string
        except Exception as e:
            continue

        if category == '图片':
            continue

        year = url.split('/')[-3]
        date_time = item.find('div', class_="dd_time").string
        date_time = '%s-%s:00' % (year, date_time)
        naive_time = dateparse.parse_datetime(date_time)
        aware_time = pytz.timezone('Asia/Shanghai').localize(naive_time, is_dst=None)
        news_info = [aware_time, "http://www.chinanews.com" + url, title]
        news_pool.append(news_info)
    return news_pool


def get_news_pool(start_date, end_date):
    news_pool = []
    delta = timedelta(days=1)
    while start_date < end_date:
        date_str = start_date.strftime("%Y/%m%d")
        page_url = 'http://www.chinanews.com/scroll-news/%s/news.shtml' % (date_str)
        logger.info('Extracting news urls at %s' % date_str)
        news_pool += get_one_page_news(page_url)

        start_date += delta
    return news_pool


def crawl_news(news_pool, min_body_len):
    crawled_news = 0
    for n, news in enumerate(news_pool):
        logger.debug('%d/%d' % (n, len(news_pool)))

        req = urllib.request.Request(news[1], headers=headers)
        try:
            response = urllib.request.urlopen(req, timeout=10)
            html = response.read()
        #            response = urllib.request.urlopen(news[1])
        except socket.timeout as err:
            logger.debug('socket.timeout')
            logger.debug(err)
            logger.debug("Sleeping for 5 minute")
            time.sleep(300)
            continue
        except Exception as e:
            logger.debug("--open url---%s:%s %s-----" % (type(e), e, news[1]))
            logger.debug("Sleeping for 5 minute")
            time.sleep(300)
            continue

        soup = BeautifulSoup(html, "html.parser")  # http://www.crummy.com/software/BeautifulSoup/bs4/doc.zh/
        [s.extract() for s in soup('script')]

        try:
            ps = soup.find('div', class_="left_zw").find_all('p')
        except Exception as e:
            logger.debug("--parse url---%s: %s-----" % (type(e), news[1]))
            logger.debug("Sleeping for 1 minute")
            time.sleep(60)
            continue

        body = ''
        for p in ps:
            cur = p.get_text().strip()
            if cur == '':
                continue
            body += '\t' + cur + '\n'
        body = body.replace(" ", "")

        if keyword not in body:  # 过滤掉乱码新闻
            continue

        if len(body) <= min_body_len:
            continue

        try:
            News.objects.get(url=news[1])
        except ObjectDoesNotExist:
            news_model = News(news_id=News.objects.count() + 1, url=news[1], title=news[2], datetime=news[0], body=body)
            news_model.save()
            crawled_news += 1

        if crawled_news % 100 == 0:
            logger.debug("Wrote %d news, Sleeping for 1 minute." % (crawled_news))
            time.sleep(60)

def crawler(days, end_date = date.today()):
    delta = timedelta(days=days)
    start_date = end_date - delta
    news_pool = get_news_pool(start_date, end_date)
    logger.info('Starting to crawl %d news' % len(news_pool))
    crawl_news(news_pool, 50)
    logger.info('done!')


if __name__ == '__main__':
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "vigo.settings")
    django.setup()
    from searcher.models import News
    crawler(days=0)