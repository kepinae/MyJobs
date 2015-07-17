# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('mypartners', '__first__'),
        ('seo', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='SavedSearch',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('label', models.CharField(max_length=60, verbose_name='Search Name')),
                ('url', models.URLField(max_length=300, verbose_name='URL of Search Results')),
                ('sort_by', models.CharField(default=b'Relevance', max_length=9, verbose_name='Sort by', choices=[(b'Relevance', 'Relevance'), (b'Date', 'Date')])),
                ('feed', models.URLField(max_length=300)),
                ('is_active', models.BooleanField(default=True, verbose_name='Search is Active')),
                ('email', models.EmailField(max_length=255, verbose_name='Which Email Address')),
                ('frequency', models.CharField(default=b'W', max_length=2, verbose_name='Frequency', choices=[(b'D', 'Daily'), (b'W', 'Weekly'), (b'M', 'Monthly')])),
                ('day_of_month', models.IntegerField(blank=True, null=True, verbose_name='on', choices=[(1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6), (7, 7), (8, 8), (9, 9), (10, 10), (11, 11), (12, 12), (13, 13), (14, 14), (15, 15), (16, 16), (17, 17), (18, 18), (19, 19), (20, 20), (21, 21), (22, 22), (23, 23), (24, 24), (25, 25), (26, 26), (27, 27), (28, 28), (29, 29), (30, 30)])),
                ('day_of_week', models.CharField(blank=True, max_length=2, null=True, verbose_name='on', choices=[(b'1', 'Monday'), (b'2', 'Tuesday'), (b'3', 'Wednesday'), (b'4', 'Thursday'), (b'5', 'Friday'), (b'6', 'Saturday'), (b'7', 'Sunday')])),
                ('jobs_per_email', models.PositiveSmallIntegerField(default=5, verbose_name='Jobs per Email', choices=[(5, 5), (10, 10), (20, 20), (30, 30), (40, 40), (50, 50), (60, 60), (70, 70), (80, 80), (90, 90), (100, 100)])),
                ('notes', models.TextField(null=True, verbose_name='Comments', blank=True)),
                ('last_sent', models.DateTimeField(null=True, editable=False, blank=True)),
                ('custom_message', models.TextField(max_length=300, null=True, blank=True)),
            ],
            options={
                'verbose_name_plural': 'saved searches',
            },
            bases=(models.Model,),
        ),
    ]
