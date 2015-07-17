# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('seo', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='Report',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=50)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('order_by', models.CharField(default=b'', max_length=50, blank=True)),
                ('app', models.CharField(default=b'mypartners', max_length=50)),
                ('model', models.CharField(default=b'contactrecord', max_length=50)),
                ('values', models.CharField(default=b'[]', max_length=500)),
                ('params', models.TextField()),
                ('results', models.FileField(upload_to=b'reports')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, null=True)),
                ('owner', models.ForeignKey(to='seo.Company')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
