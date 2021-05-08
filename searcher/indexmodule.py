import math

import django
import os
import configparser
import jieba
from django.utils import timezone
from django.utils.timezone import datetime
from searcher.models import News, Indexs
from django.db.models import ObjectDoesNotExist


class Doc:
    docid = 0
    date_time = ''
    term_frequency = 0
    len = 0

    def __init__(self, docid, date_time, tf, len):
        self.docid = docid
        self.date_time = date_time
        self.term_frequency = tf
        self.len = len

    def __repr__(self):
        return (str(self.docid) + '\t' + self.date_time + '\t' + str(self.term_frequency) + '\t' + str(self.len))

    def __str__(self):
        return (str(self.docid) + '\t' + self.date_time + '\t' + str(self.term_frequency) + '\t' + str(self.len))


class IndexModule:
    stop_words = set()
    postings_lists = {}

    config_path = ''
    config_encoding = ''

    def __init__(self, config_path, config_encoding):
        self.config_path = config_path
        self.config_encoding = config_encoding
        config = configparser.ConfigParser()
        config.read(filenames=config_path, encoding=config_encoding)
        f = open(config['INDEX']['stop_words_path'], encoding=config['INDEX']['stop_words_encoding'])
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

    def clean_list(self, seg_list):
        cleaned_dict = {}  # map: words -> count
        total_words = 0
        for term in seg_list:
            term = term.strip().lower()
            if term != '' and not self.is_number(term) and term not in self.stop_words:
                total_words += 1
                if term in cleaned_dict:
                    cleaned_dict[term] += 1
                else:
                    cleaned_dict[term] = 1
        return total_words, cleaned_dict

    def write_postings_to_db(self):
        for key, value in self.postings_lists.items():
            doc_list = '\n'.join(map(str, value[1]))
            try:
                index = Indexs.objects.get(term=key)
                index.df += value[0]
                index.docs += '\n' + doc_list
            except ObjectDoesNotExist:
                index = Indexs(term=key, df=value[0], docs=doc_list)

            index.save()

    def construct_postings_lists(self, day_before=1, end_date=datetime.today().date()):
        config = configparser.ConfigParser()
        config.read(self.config_path, self.config_encoding)

        # files = News.objects.filter(datetime__day=timezone.now().day - day_before)
        files = News.objects.filter(
            datetime__gte=end_date - timezone.timedelta(days=day_before),
            datetime__lte=end_date)
        total_len = int(config['FORMULA']['avg_l']) * int(config['FORMULA']['n'])
        for file in files:
            title = file.title
            body = file.body
            docid = file.pk
            date_time = file.datetime.strftime('%y-%m-%d %H:%M:%S')
            seg_list = jieba.lcut_for_search(title + '。' + body)

            total_words, cleaned_dict = self.clean_list(seg_list)

            total_len += total_words

            for term, tf_in_doc in cleaned_dict.items():
                if term in title:
                    tf_in_doc += int(math.log2(total_words))
                d = Doc(docid, date_time, tf_in_doc, total_words)
                if term in self.postings_lists:  # if term in dict, append doc
                    self.postings_lists[term][0] += 1   # doc_frequency++
                    self.postings_lists[term][1].append(d)
                else:  # else create new term and insert doc
                    self.postings_lists[term] = [1, [d]]  # [doc_frequency, [Doc]]
        AVG_L = int(total_len / News.objects.count())
        config.set('FORMULA', 'n', str(News.objects.count()))
        config.set('FORMULA', 'avg_l', str(AVG_L))
        with open(self.config_path, 'w', encoding=self.config_encoding) as configfile:
            config.write(configfile)
        self.write_postings_to_db()


def create_index(config, encoding, days, end_date):
    index = IndexModule(config, encoding)
    index.construct_postings_lists(days, end_date)


if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "vigo.settings")
    django.setup()
    from searcher.models import News, Indexs
    index = IndexModule('../config.ini', 'utf-8')
    index.construct_postings_lists(1)
    print('create index done!')
