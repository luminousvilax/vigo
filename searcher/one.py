from django.utils import dateparse, timezone
import pytz
import os,django
import sqlite3
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "vigo.settings")
django.setup()
from searcher.models import News, Indexs
from datetime import date

if __name__ == '__main__':
 start_date = timezone.datetime.today().date()-timezone.timedelta(1)
 #end_date = timezone.datetime.today().date()-timezone.timedelta(0)
 end_date = timezone.datetime.now()
 print(start_date)
 print(end_date)
 files = News.objects.filter(datetime__gte=start_date, datetime__lte=end_date)
 count = 0
 for file in files:
   count+=1

 print(count)