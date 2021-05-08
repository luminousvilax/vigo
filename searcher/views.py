from typing import List

from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.utils import timezone
from searcher.search_engine import SearchEngine
from searcher.models import News
import os

keyword = ''
news_list = []
pages = []
sort_type = ''
use_time = ''
counts = 0

def index(request):
    return render(request, 'searcher/index.html')

def results(request):
    try:
        global keyword, news_list, pages, sort_type, use_time, counts
        start_time = timezone.datetime.now()
        se = SearchEngine('./config.ini', 'utf-8', 'SEARCH')
        keyword = request.POST['keyword']
        try:
            sort_type = request.POST['order']
        except KeyError:
            sort_type = 'related'
        flag, result = se.search(keyword, sort_type)

        news_list = [News.objects.get(pk=res[0]) for res in result]
        pages = []
        for i in range(1, len(news_list) // 10 + 2):
            pages.append(i)

        first_page_news = cut_page(1)
        page_order = pageorder(pages, 1)
        use_time = (timezone.datetime.now() - start_time).total_seconds()
        counts = len(news_list)
        context = {
            'keyword': keyword,
            'result': first_page_news,
            'pages': pages,
            'pageorder': page_order,
            'sort': sort_type,
            'use_time': use_time,
            'counts': counts
        }
        return render(request, 'searcher/results.html', context)
    except:
        return render(request, 'searcher/error.html')

def details(request, pk):
    try:
        doc = News.objects.get(pk=pk)
        contents = doc.body.split('\n')
        if doc.similar == '':
            return render(request, 'searcher/detail.html', context={'doc': doc, 'contents': contents})
        similar_list = doc.similar.split(',')
        similar_news = []
        for sim in similar_list[:6]:
            sim_news = News.objects.get(pk=int(sim))
            similar_news.append(sim_news)
        context = {'doc': doc, 'contents': contents, 'similar_news': similar_news}
        return render(request, 'searcher/detail.html', context)
    except:
        return render(request, 'searcher/error.html')


def next_page(request, page_order):
    try:
        global pages, keyword, sort_type, use_time, counts
        page_news = cut_page(page_order)
        context = {
            'keyword': keyword,
            'result': page_news,
            'pages': pages,
            'pageorder': pageorder(pages, page_order),
            'sort': sort_type,
            'use_time': use_time,
            'counts': counts
        }
        return render(request, 'searcher/results.html', context)
    except:
        return render(request, 'searcher/error.html')

def cut_page(page_order):
    global news_list
    one_page_news = news_list[(page_order-1)*10 : page_order*10]
    return one_page_news

class pageorder:
    pre_order = 0
    cur_order = 1
    next_order = 2
    max_order = 0

    def __init__(self, pages, order):
        self.cur_order = order
        self.pre_order = order-1
        self.next_order = order+1
        self.max_order = pages[-1]

    def is_first(self):
        return self.cur_order == 1

    def is_max(self):
        return self.cur_order == self.max_order
