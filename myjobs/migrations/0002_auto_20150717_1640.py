# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0001_initial'),
        ('mysearches', '0001_initial'),
        ('myjobs', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='emaillog',
            name='send_log',
            field=models.ForeignKey(related_name='sendgrid_response', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='mysearches.SavedSearchLog', help_text=b'Entries prior to the\n                                 release of saved search logging will\n                                 have no categories, meaning we cannot\n                                 match them with a SendGrid\n                                 response.', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='user',
            name='groups',
            field=models.ManyToManyField(related_query_name='user', related_name='user_set', to='auth.Group', blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of his/her group.', verbose_name='groups'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='user',
            name='user_permissions',
            field=models.ManyToManyField(related_query_name='user', related_name='user_set', to='auth.Permission', blank=True, help_text='Specific permissions for this user.', verbose_name='user permissions'),
            preserve_default=True,
        ),
    ]
