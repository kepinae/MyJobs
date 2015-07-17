# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import mymessages.models


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('subject', models.CharField(max_length=200, verbose_name=b'Subject')),
                ('message_type', models.CharField(max_length=200, verbose_name=b'Message type', choices=[(b'error', b'Error'), (b'info', b'Info'), (b'block', b'Notice'), (b'success', b'Success')])),
                ('body', models.TextField(verbose_name=b'Body')),
                ('start_on', models.DateTimeField(default=mymessages.models.start_default, verbose_name=b'Start on')),
                ('expire_at', models.DateTimeField(default=mymessages.models.expire_default, help_text=b'Default is two weeks after message is sent.', null=True, verbose_name=b'Expire at', db_index=True)),
                ('btn_text', models.CharField(default=b'OK', max_length=100, verbose_name=b'Button text')),
                ('system', models.BooleanField(default=False, help_text=b'This is a system message and appears as an alert as well as in the inbox.', verbose_name=b'System message')),
                ('group', models.ManyToManyField(to='auth.Group')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MessageInfo',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('read', models.BooleanField(default=False, db_index=True)),
                ('read_at', models.DateTimeField(null=True, verbose_name=b'read at')),
                ('expired', models.BooleanField(default=False, db_index=True)),
                ('expired_on', models.DateTimeField(null=True, verbose_name=b'expired on')),
                ('deleted_on', models.DateTimeField(db_index=True, null=True, verbose_name=b'deleted on', blank=True)),
                ('message', models.ForeignKey(to='mymessages.Message')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='messageinfo',
            unique_together=set([('user', 'message')]),
        ),
        migrations.AddField(
            model_name='message',
            name='users',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL, through='mymessages.MessageInfo'),
            preserve_default=True,
        ),
    ]
