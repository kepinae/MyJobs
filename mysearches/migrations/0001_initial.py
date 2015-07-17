# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('mypartners', '__first__'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
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
        migrations.CreateModel(
            name='PartnerSavedSearch',
            fields=[
                ('savedsearch_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='mysearches.SavedSearch')),
                ('url_extras', models.CharField(help_text=b'Anything you put here will be added as query string parameters to each of links in the saved search.', max_length=255, blank=True)),
                ('partner_message', models.TextField(help_text=b'Use this field to provide a customized greeting that will be sent with each copy of this saved search.', blank=True)),
                ('unsubscribed', models.BooleanField(default=False)),
                ('unsubscriber', models.EmailField(verbose_name=b'Unsubscriber', max_length=255, editable=False, blank=True)),
                ('created_by', models.ForeignKey(related_name='created_by', on_delete=django.db.models.deletion.SET_NULL, editable=False, to=settings.AUTH_USER_MODEL, null=True)),
                ('partner', models.ForeignKey(to='mypartners.Partner')),
                ('provider', models.ForeignKey(to='seo.Company')),
                ('tags', models.ManyToManyField(to='mypartners.Tag', null=True)),
            ],
            options={
            },
            bases=('mysearches.savedsearch',),
        ),
        migrations.CreateModel(
            name='SavedSearchDigest',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('is_active', models.BooleanField(default=False)),
                ('email', models.EmailField(max_length=255)),
                ('frequency', models.CharField(default=b'D', max_length=2, verbose_name='How often:', choices=[(b'D', 'Daily'), (b'W', 'Weekly'), (b'M', 'Monthly')])),
                ('day_of_month', models.IntegerField(blank=True, null=True, verbose_name='on', choices=[(1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6), (7, 7), (8, 8), (9, 9), (10, 10), (11, 11), (12, 12), (13, 13), (14, 14), (15, 15), (16, 16), (17, 17), (18, 18), (19, 19), (20, 20), (21, 21), (22, 22), (23, 23), (24, 24), (25, 25), (26, 26), (27, 27), (28, 28), (29, 29), (30, 30)])),
                ('day_of_week', models.CharField(blank=True, max_length=2, null=True, verbose_name='on', choices=[(b'1', 'Monday'), (b'2', 'Tuesday'), (b'3', 'Wednesday'), (b'4', 'Thursday'), (b'5', 'Friday'), (b'6', 'Saturday'), (b'7', 'Sunday')])),
                ('send_if_none', models.BooleanField(default=False, verbose_name='Send even if there are no results', editable=False)),
                ('user', models.OneToOneField(editable=False, to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SavedSearchLog',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('was_sent', models.BooleanField()),
                ('was_received', models.BooleanField(default=False, help_text=b'If date_sent is very recent and was_received is unchecked, SendGrid may not have responded yet - give it a few minutes.')),
                ('reason', models.TextField()),
                ('recipient_email', models.EmailField(max_length=255)),
                ('new_jobs', models.IntegerField()),
                ('backfill_jobs', models.IntegerField()),
                ('date_sent', models.DateTimeField(auto_now_add=True)),
                ('uuid', models.CharField(max_length=32, db_index=True)),
                ('contact_record', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, blank=True, to='mypartners.ContactRecord', null=True)),
                ('recipient', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='savedsearch',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, editable=False, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
    ]
