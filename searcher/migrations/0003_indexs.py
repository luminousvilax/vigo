# Generated by Django 3.1.7 on 2021-05-06 07:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('searcher', '0002_news_similar'),
    ]

    operations = [
        migrations.CreateModel(
            name='Indexs',
            fields=[
                ('term', models.CharField(max_length=100, primary_key=True, serialize=False)),
                ('df', models.IntegerField(default=0)),
                ('docs', models.TextField()),
            ],
        ),
    ]