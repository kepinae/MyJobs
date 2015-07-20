# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('myreports', '0001_initial'),
        ('seo', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='report',
            name='owner',
            field=models.ForeignKey(to='seo.Company'),
            preserve_default=True,
        ),
    ]
