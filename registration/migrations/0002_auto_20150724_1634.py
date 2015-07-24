# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('registration', '0001_initial'),
        ('seo', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='invitation',
            name='inviting_company',
            field=models.ForeignKey(related_name='invites_sent', blank=True, to='seo.Company', null=True),
        ),
        migrations.AddField(
            model_name='invitation',
            name='inviting_user',
            field=models.ForeignKey(related_name='invites_sent', editable=False, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AddField(
            model_name='activationprofile',
            name='user',
            field=models.ForeignKey(verbose_name=b'user', to=settings.AUTH_USER_MODEL),
        ),
    ]
