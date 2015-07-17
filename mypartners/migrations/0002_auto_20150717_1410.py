# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('mypartners', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Status',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('code', models.PositiveSmallIntegerField(default=1, verbose_name=b'Status Code', choices=[(0, b'Unprocessed'), (1, b'Approved'), (2, b'Denied')])),
                ('last_modified', models.DateTimeField(auto_now=True, verbose_name=b'Last Modified')),
                ('approved_by', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),

        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('hex_color', models.CharField(default=b'd4d4d4', max_length=6, blank=True)),
                ('created_on', models.DateTimeField(auto_now=True)),
                ('company', models.ForeignKey(to='seo.Company')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'verbose_name': 'tag',
            },
            bases=(models.Model,),
        ),

        migrations.AddField(
            model_name='contactrecord',
            name='created_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),

        migrations.AddField(
            model_name='contactlogentry',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),

        migrations.AddField(
            model_name='contact',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, blank=True, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),

        migrations.AlterUniqueTogether(
            name='tag',
            unique_together=set([('name', 'company')]),
        ),

        migrations.AddField(
            model_name='partner',
            name='tags',
            field=models.ManyToManyField(to='mypartners.Tag', null=True),
            preserve_default=True,
        ),

        migrations.AddField(
            model_name='contactrecord',
            name='tags',
            field=models.ManyToManyField(to='mypartners.Tag', null=True),
            preserve_default=True,
        ),

        migrations.AddField(
            model_name='contact',
            name='tags',
            field=models.ManyToManyField(to='mypartners.Tag', null=True),
            preserve_default=True,
        ),
    ]
