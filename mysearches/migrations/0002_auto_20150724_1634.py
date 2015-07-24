# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mysearches', '0001_initial'),
        ('mypartners', '0001_initial'),
        ('seo', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='partnersavedsearch',
            name='provider',
            field=models.ForeignKey(to='seo.Company'),
        ),
        migrations.AddField(
            model_name='partnersavedsearch',
            name='tags',
            field=models.ManyToManyField(to='mypartners.Tag'),
        ),
    ]
