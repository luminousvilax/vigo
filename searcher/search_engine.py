import configparser
import django
import math
import operator
import os
from datetime import *

import jieba
from django.db.models import ObjectDoesNotExist
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "vigo.settings")
django.setup()
from searcher.models import News, Indexs


class SearchEngine:
    stop_words = set()

    config_path = ''
    config_encoding = ''

    K1 = 0
    B = 0
    N = 0
    AVG_L = 0

    HOT_K1 = 0
    HOT_K2 = 0

    def __init__(self, config_path, config_encoding, mode):
        self.config_path = config_path
        self.config_encoding = config_encoding
        config = configparser.ConfigParser()
        config.read(config_path, config_encoding)
        f = open(config[mode]['stop_words_path'], encoding=config[mode]['stop_words_encoding'])
        words = f.read()
        self.stop_words = set(words.split('\n'))
        self.K1 = float(config['FORMULA']['k1'])
        self.B = float(config['FORMULA']['b'])
        self.N = int(config['FORMULA']['n'])
        self.AVG_L = float(config['FORMULA']['avg_l'])
        self.HOT_K1 = float(config['FORMULA']['hot_k1'])
        self.HOT_K2 = float(config['FORMULA']['hot_k2'])

    def is_number(self, s):
        try:
            float(s)
            return True
        except ValueError:
            return False

    def sigmoid(self, x):
        return 1 / (1 + math.exp(-x))

    def clean_list(self, seg_list):
        cleaned_dict = {}
        terms = 0
        for i in seg_list:
            i = i.strip().lower()
            if i != '' and not self.is_number(i) and i not in self.stop_words:
                terms = terms + 1
                if i in cleaned_dict:
                    cleaned_dict[i] = cleaned_dict[i] + 1
                else:
                    cleaned_dict[i] = 1
        return terms, cleaned_dict

    def search(self, sentence, sort_type='related'):
        seg_list = jieba.lcut(sentence, cut_all=False)
        terms, cleaned_dict = self.clean_list(seg_list)
        scores = {}
        for term in cleaned_dict.keys():
            try:
                record = Indexs.objects.get(term=term)
            except ObjectDoesNotExist:
                continue
            df = record.df
            docs = record.docs.split('\n')
            idf = math.log((self.N - df + 0.5) / (df + 0.5) + 1)

            if sort_type == 'related':
                self.result_BM25(scores, docs, idf)
            elif sort_type == 'hot':
                self.result_hot(scores, docs, idf)
            elif sort_type == 'time':
                self.result_time(scores, docs)

        scores = sorted(scores.items(), key=operator.itemgetter(1))
        scores.reverse()
        if len(scores) == 0:
            return 0, []
        else:
            return 1, scores

    def result_BM25(self, scores, docs, idf):
        for doc in docs:
            docid, date_time, tf, ld = doc.split('\t')
            docid = int(docid)
            tf = int(tf)
            ld = int(ld)
            score = ((self.K1 + 1) * tf * idf) / (tf + self.K1 * (1 - self.B + self.B * ld / self.AVG_L))
            if docid in scores:
                scores[docid] = scores[docid] + score
            else:
                scores[docid] = score

    def result_hot(self, scores, docs, idf):
        for doc in docs:
            docid, date_time, tf, ld = doc.split('\t')
            docid = int(docid)
            tf = int(tf)
            ld = int(ld)
            news_datetime = datetime.strptime(date_time, "%y-%m-%d %H:%M:%S")
            now_datetime = datetime.now()
            td = now_datetime - news_datetime
            BM25_score = (self.K1 * tf * idf) / (tf + self.K1 * (1 - self.B + self.B * ld / self.AVG_L))
            td = (timedelta.total_seconds(td) / 3600)
            hot_score = self.HOT_K1 * self.sigmoid(BM25_score) + self.HOT_K2 / td
            if docid in scores:
                scores[docid] = scores[docid] + hot_score
            else:
                scores[docid] = hot_score

    def result_time(self, scores, docs):
        for doc in docs:
            docid, date_time, tf, ld = doc.split('\t')
            if docid in scores:
                continue
            news_datetime = datetime.strptime(date_time, "%y-%m-%d %H:%M:%S")
            now_datetime = datetime.now()
            td = now_datetime - news_datetime
            docid = int(docid)
            td = (timedelta.total_seconds(td) / 3600)  # hour
            scores[docid] = td

if __name__ == "__main__":
    se = SearchEngine('../config.ini', 'utf-8', 'INDEX')
    words = input('Search for: ')
    flag, result = se.search(words, 0)
    for res in result[:10]:
        news = News.objects.get(pk=res[0])
        print(news.title)
    #print(result[:10])