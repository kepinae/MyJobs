# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0001_initial'),
        ('mysearches', '__first__'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('seo', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ActivationProfile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('activation_key', models.CharField(max_length=40, verbose_name='activation_key')),
                ('email', models.EmailField(max_length=255)),
                ('sent', models.DateTimeField(default=django.utils.timezone.now, auto_now_add=True)),
                ('user', models.ForeignKey(verbose_name=b'user', to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
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
                ('inviting_company', models.ForeignKey(related_name='invites_sent', blank=True, to='seo.Company', null=True)),
                ('inviting_user', models.ForeignKey(related_name='invites_sent', editable=False, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
