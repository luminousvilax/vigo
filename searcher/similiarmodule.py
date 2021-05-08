import os

import django
import jieba
import jieba.analyse
import configparser
from datetime import *
import math

import pandas as pd
import numpy as np
from searcher.models import News
from sklearn.metrics import pairwise_distances
from django.utils import timezone


class SimiliarModule:
    stop_words = set()
    k_nearest = []

    config_path = ''
    config_encoding = ''

    stop_words_path = ''
    stop_words_encoding = ''
    idf_path = ''

    def __init__(self, config_path, config_encoding):
        self.config_path = config_path
        self.config_encoding = config_encoding
        config = configparser.ConfigParser()
        config.read(config_path, config_encoding)

        self.stop_words_path = config['INDEX']['stop_words_path']
        self.stop_words_encoding = config['INDEX']['stop_words_encoding']
        self.idf_path = config['INDEX']['idf_path']

        f = open(self.stop_words_path, encoding=self.stop_words_encoding)
        words = f.read()
        self.stop_words = set(words.split('\n'))

    def is_number(self, s):
        try:
            float(s)
            return True
        except ValueError:
            if s[-1] == '%':
                return True
            return False

    def generate_idf_file(self, files):
        n = float(len(files))
        idf = {}
        for news in files:
            title = news.title
            body = news.body
            seg_list = jieba.lcut(title + '。' + body, cut_all=False)
            seg_list = set(seg_list) - self.stop_words
            for word in seg_list:
                word = word.strip().lower()
                if word == '' or self.is_number(word):
                    continue
                if word not in idf:
                    idf[word] = 1
                else:
                    idf[word] += 1
        idf_file = open(self.idf_path, 'w', encoding='utf-8')
        for word, df in idf.items():
            value = math.log((n - df + 0.5) / (df + 0.5) + 1)
            idf_file.write('%s %.9f\n' % (word, value))
        idf_file.close()

    def construct_dt_matrix(self, files, topK=20):
        jieba.analyse.set_stop_words(self.stop_words_path)
        jieba.analyse.set_idf_path(self.idf_path)
        row = len(files)
        columns = 1
        terms = {}
        dt = []
        for news in files:
            title = news.title
            body = news.body
            docid = news.pk
            tags = jieba.analyse.extract_tags(title + '。' + body, topK=topK, withWeight=True)
            cleaned_dict = {}
            for word, tfidf in tags:
                word = word.strip().lower()
                if word == '' or self.is_number(word):
                    continue
                cleaned_dict[word] = tfidf
                if word not in terms:
                    terms[word] = columns
                    columns += 1
            dt.append([docid, cleaned_dict])
        dt_matrix = [[0 for i in range(columns)] for j in range(row)]
        i = 0
        for docid, t_tfidf in dt:
            dt_matrix[i][0] = docid
            for word, tfidf in t_tfidf.items():
                dt_matrix[i][terms[word]] = tfidf
            i += 1

        dt_matrix = pd.DataFrame(dt_matrix)
        dt_matrix.index = dt_matrix[0]
        print('dt_matrix shape:(%d %d)' % (dt_matrix.shape))
        print(dt_matrix.head())
        return dt_matrix

    def construct_k_nearest_matrix(self, dt_matrix, k):
        distances = pairwise_distances(dt_matrix[dt_matrix.columns[1:]], metric="cosine")
        tmp = np.array(1 - distances)
        similarity_matrix = pd.DataFrame(tmp, index=dt_matrix.index.tolist(), columns=dt_matrix.index.tolist())
        for row in similarity_matrix.index:
            tmp = [int(row), []]
            j = 0
            while j < k:
                max_col = similarity_matrix.loc[row].idxmax(axis=1)  # get the most similar doc id
                similarity_matrix.loc[row][max_col] = -1
                if max_col != row:
                    tmp[1].append(str(max_col))  # max_col is similar doc id
                    j += 1
            self.k_nearest.append(tmp)

    def write_k_nearest_matrix_to_db(self):
        for doc_id, sim_list in self.k_nearest:
            news = News.objects.get(pk=doc_id)
            similar = ','.join(sim_list)
            news.similar = similar
            news.save()

    def find_k_nearest(self, k, topK, days=14, end_date=timezone.datetime.today().date()):
        files = News.objects.filter(datetime__gte=end_date - timedelta(days=days))
        self.generate_idf_file(files)
        dt_matrix = self.construct_dt_matrix(files, topK)
        self.construct_k_nearest_matrix(dt_matrix, k)
        self.write_k_nearest_matrix_to_db()


def create_similar(config, encoding, days=14, end_date=timezone.datetime.today().date()):
    sm = SimiliarModule(config, encoding)
    sm.find_k_nearest(10, 25, days, end_date)


if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "vigo.settings")
    django.setup()
    from searcher.models import News
    print('-----start time: %s-----' % (datetime.today()))
    sm = SimiliarModule('../config.ini', 'utf-8')
    sm.find_k_nearest(10, 25, 14)
    print('-----finish time: %s-----' % (datetime.today()))
