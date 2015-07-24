# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('mysearches', '0001_initial'),
        ('auth', '0006_require_contenttypes_0002'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ActivationProfile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('activation_key', models.CharField(max_length=40, verbose_name='activation_key')),
                ('email', models.EmailField(max_length=255)),
                ('sent', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='Invitation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('invitee_email', models.CharField(max_length=255, db_index=True)),
                ('invited', models.DateTimeField(auto_now_add=True)),
                ('accepted', models.BooleanField(default=False, help_text=b'Has the invitee accepted this invitation', editable=False)),
                ('added_permission', models.ForeignKey(blank=True, to='auth.Group', null=True)),
                ('added_saved_search', models.ForeignKey(blank=True, editable=False, to='mysearches.SavedSearch', null=True)),
                ('invitee', models.ForeignKey(related_name='invites', on_delete=django.db.models.deletion.SET_NULL, editable=False, to=settings.AUTH_USER_MODEL, null=True)),
            ],
        ),
    ]
