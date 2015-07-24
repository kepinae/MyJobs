# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('mysearches', '0002_auto_20150724_1634'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='savedsearchdigest',
            name='user',
            field=models.OneToOneField(editable=False, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='savedsearchlog',
            name='recipient',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AddField(
            model_name='partnersavedsearch',
            name='created_by',
            field=models.ForeignKey(related_name='created_by', on_delete=django.db.models.deletion.SET_NULL, editable=False, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AddField(
            model_name='savedsearch',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, editable=False, to=settings.AUTH_USER_MODEL, null=True),
        ),
    ]
