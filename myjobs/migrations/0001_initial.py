# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0001_initial'),
        ('sites', '0001_initial'),
        ('mysearches', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(default=django.utils.timezone.now, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('email', models.EmailField(unique=True, max_length=255, verbose_name='email address', db_index=True)),
                ('date_joined', models.DateTimeField(auto_now_add=True, verbose_name='date joined')),
                ('gravatar', models.EmailField(db_index=True, max_length=255, verbose_name='gravatar email', blank=True)),
                ('profile_completion', models.IntegerField(default=0, validators=[django.core.validators.MaxValueValidator(100), django.core.validators.MinValueValidator(0)])),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this corresponds to a validemail address. Deselect thisinstead of deleting accounts.', verbose_name='active')),
                ('is_disabled', models.BooleanField(default=False, verbose_name='disabled')),
                ('is_verified', models.BooleanField(default=False, help_text='User has verified this address and can access most My.jobs features. Deselect this instead of deleting accounts.', verbose_name='verified')),
                ('in_reserve', models.BooleanField(default=False, help_text='This user will be held in reserve until any invitations associated with it are processed.', verbose_name='reserved', editable=False)),
                ('opt_in_myjobs', models.BooleanField(default=True, help_text='Checking this allows My.jobs to send email updates to you.', verbose_name='Opt-in to non-account emails and Saved Search')),
                ('opt_in_employers', models.BooleanField(default=True, help_text='Checking this allows employers to send emails to you.', verbose_name='Email is visible to Employers')),
                ('last_response', models.DateField(default=datetime.datetime.now, blank=True)),
                ('password_change', models.BooleanField(default=False, verbose_name='Password must be changed on next login')),
                ('user_guid', models.CharField(unique=True, max_length=100, db_index=True)),
                ('first_name', models.CharField(max_length=255, blank=True)),
                ('last_name', models.CharField(max_length=255, blank=True)),
                ('timezone', models.CharField(default=b'America/New_York', max_length=255)),
                ('source', models.CharField(default=b'https://secure.my.jobs', help_text='Site that initiated account creation', max_length=255)),
                ('deactivate_type', models.CharField(default=b'none', max_length=11, choices=[(b'none', b'none'), (b'dropped', b'dropped'), (b'bounce', b'bounce'), (b'unsubscribe', b'unsubscribe'), (b'spamreport', b'spamreport')])),
                ('groups', models.ManyToManyField(related_query_name='user', related_name='user_set', to='auth.Group', blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of his/her group.', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(related_query_name='user', related_name='user_set', to='auth.Permission', blank=True, help_text='Specific permissions for this user.', verbose_name='user permissions')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CustomHomepage',
            fields=[
                ('site_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='sites.Site')),
                ('logo_url', models.URLField(null=True, verbose_name=b'Logo Image URL', blank=True)),
                ('show_signup_form', models.BooleanField(default=True)),
            ],
            options={
            },
            bases=('sites.site',),
        ),
        migrations.CreateModel(
            name='EmailLog',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('email', models.EmailField(max_length=254)),
                ('event', models.CharField(max_length=11)),
                ('received', models.DateField()),
                ('processed', models.BooleanField(default=False)),
                ('category', models.CharField(max_length=255, blank=True)),
                ('reason', models.TextField(blank=True)),
                ('send_log', models.ForeignKey(related_name='sendgrid_response', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='mysearches.SavedSearchLog', help_text=b'Entries prior to the\n                                 release of saved search logging will\n                                 have no categories, meaning we cannot\n                                 match them with a SendGrid\n                                 response.', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='FAQ',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('question', models.CharField(max_length=255, verbose_name=b'Question')),
                ('answer', models.TextField(help_text=b'Answers allow use of HTML', verbose_name=b'Answer')),
                ('is_visible', models.BooleanField(default=True, verbose_name=b'Is visible')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Shared_Sessions',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('session', models.TextField(blank=True)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, unique=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Ticket',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('ticket', models.CharField(max_length=255)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='ticket',
            unique_together=set([('ticket', 'user')]),
        ),
    ]
