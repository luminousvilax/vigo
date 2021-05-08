from django.db import models

class News(models.Model):
    news_id = models.IntegerField(default=0)
    url = models.CharField(max_length=200)
    title = models.CharField(max_length=100)
    datetime = models.DateTimeField('date published')
    body = models.TextField()
    similar = models.CharField(max_length=100, default='')

    def __str__(self):
        return ('#' + self.title)

class Indexs(models.Model):
    term = models.CharField(max_length=100, primary_key=True)
    df = models.IntegerField(default=0)
    docs = models.TextField()

    def __str__(self):
        return (self.term)