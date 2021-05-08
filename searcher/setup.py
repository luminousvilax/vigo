import os
import sys, getopt
import logging

import django
from django.utils.timezone import datetime
from django.utils import timezone

logger = logging.getLogger('vigo')

def main(argv):
    days = 1
    end_delta = 0
    config_path = '../config.ini'
    encoding = 'utf-8'

    try:
        opts, args = getopt.getopt(argv, "d:e:")
    except:
        print('faild to resolve args')

    for opt, arg in opts:
        if opt in ['-d']:
            days = int(arg)
        if opt in ['-e']:
            end_delta = int(arg)

    end_date = datetime.today().date() - timezone.timedelta(end_delta)

    logger.info('=========Crawl News=========')
    logger.info('start time: ' + timestamp_now())
    crawler(days, end_date)
    logger.info('days: ' + str(days))
    logger.info('end time: ' + timestamp_now())

    logger.info('==========Create Index=========')
    logger.info('start time: ' + timestamp_now())
    create_index(config_path, encoding, days, end_date)
    logger.info('end time: ' + timestamp_now())

    logger.info('===========Create Similar============')
    logger.info('start time: ' + timestamp_now())
    create_similar(config_path, encoding)
    logger.info('end time: ' + timestamp_now() + '\n')
    logger.info('done!\n')

    print('finish')

def timestamp_now():
    return timezone.datetime.now().strftime('%y-%m-%d %H:%M:%S')

if __name__ == '__main__':
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "vigo.settings")
    django.setup()
    from searcher.crawler import crawler
    from searcher.indexmodule import create_index
    from searcher.similiarmodule import create_similar
    main(sys.argv[1:])