# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('seo', '0002_auto_20150724_1634'),
    ]

    operations = [
        migrations.CreateModel(
            name='CreatedEvent',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('is_active', models.BooleanField(default=True)),
                ('name', models.CharField(max_length=255)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='CronEvent',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('is_active', models.BooleanField(default=True)),
                ('name', models.CharField(max_length=255)),
                ('field', models.CharField(max_length=255, blank=True)),
                ('minutes', models.IntegerField()),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='EmailSection',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('section_type', models.PositiveIntegerField(choices=[(1, b'Header'), (2, b'Body'), (3, b'Footer')])),
                ('content', models.TextField()),
                ('owner', models.ForeignKey(blank=True, to='seo.Company', null=True)),
            ],
        ),
        migrations.CreateModel(
            name='EmailTask',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('event_id', models.PositiveIntegerField()),
                ('completed_on', models.DateTimeField(null=True, blank=True)),
                ('scheduled_for', models.DateTimeField(default=datetime.datetime.now)),
                ('scheduled_at', models.DateTimeField(auto_now_add=True)),
                ('task_id', models.CharField(default=b'', help_text=b'guid with dashes', max_length=36, blank=True)),
                ('event_model', models.ForeignKey(related_name='email_type', to='contenttypes.ContentType')),
                ('object_model', models.ForeignKey(related_name='email_model', to='contenttypes.ContentType')),
            ],
        ),
        migrations.CreateModel(
            name='EmailTemplate',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('body', models.ForeignKey(related_name='body_for', to='myemails.EmailSection')),
                ('footer', models.ForeignKey(related_name='footer_for', to='myemails.EmailSection')),
                ('header', models.ForeignKey(related_name='header_for', to='myemails.EmailSection')),
                ('owner', models.ForeignKey(blank=True, to='seo.Company', null=True)),
            ],
        ),
        migrations.CreateModel(
            name='ValueEvent',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('is_active', models.BooleanField(default=True)),
                ('name', models.CharField(max_length=255)),
                ('compare_using', models.CharField(max_length=255, verbose_name='Comparison Type', choices=[(b'eq', b'is equal to'), (b'ge', b'is greater than or equal to'), (b'le', b'is less than or equal to')])),
                ('field', models.CharField(max_length=255)),
                ('value', models.PositiveIntegerField()),
                ('email_template', models.ForeignKey(to='myemails.EmailTemplate')),
                ('model', models.ForeignKey(to='contenttypes.ContentType')),
                ('owner', models.ForeignKey(to='seo.Company')),
                ('sites', models.ManyToManyField(to='seo.SeoSite')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='cronevent',
            name='email_template',
            field=models.ForeignKey(to='myemails.EmailTemplate'),
        ),
        migrations.AddField(
            model_name='cronevent',
            name='model',
            field=models.ForeignKey(to='contenttypes.ContentType'),
        ),
        migrations.AddField(
            model_name='cronevent',
            name='owner',
            field=models.ForeignKey(to='seo.Company'),
        ),
        migrations.AddField(
            model_name='cronevent',
            name='sites',
            field=models.ManyToManyField(to='seo.SeoSite'),
        ),
        migrations.AddField(
            model_name='createdevent',
            name='email_template',
            field=models.ForeignKey(to='myemails.EmailTemplate'),
        ),
        migrations.AddField(
            model_name='createdevent',
            name='model',
            field=models.ForeignKey(to='contenttypes.ContentType'),
        ),
        migrations.AddField(
            model_name='createdevent',
            name='owner',
            field=models.ForeignKey(to='seo.Company'),
        ),
        migrations.AddField(
            model_name='createdevent',
            name='sites',
            field=models.ManyToManyField(to='seo.SeoSite'),
        ),
    ]
