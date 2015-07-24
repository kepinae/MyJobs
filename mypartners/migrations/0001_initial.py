# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import mypartners.models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Contact',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255, verbose_name=b'Full Name')),
                ('email', models.EmailField(max_length=255, verbose_name=b'Email', blank=True)),
                ('phone', models.CharField(default=b'', max_length=30, verbose_name=b'Phone', blank=True)),
                ('notes', models.TextField(default=b'', max_length=1000, verbose_name=b'Notes', blank=True)),
                ('archived_on', models.DateTimeField(null=True)),
            ],
            options={
                'verbose_name_plural': 'contacts',
            },
        ),
        migrations.CreateModel(
            name='ContactLogEntry',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('action_flag', models.PositiveSmallIntegerField(verbose_name=b'action flag')),
                ('action_time', models.DateTimeField(auto_now=True, verbose_name=b'action time')),
                ('change_message', models.TextField(verbose_name=b'change message', blank=True)),
                ('contact_identifier', models.CharField(max_length=255)),
                ('delta', models.TextField(blank=True)),
                ('object_id', models.TextField(null=True, verbose_name=b'object id', blank=True)),
                ('object_repr', models.CharField(max_length=200, verbose_name=b'object repr')),
            ],
        ),
        migrations.CreateModel(
            name='ContactRecord',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_on', models.DateTimeField(auto_now=True)),
                ('contact_type', models.CharField(max_length=50, verbose_name=b'Contact Type', choices=[(b'email', b'Email'), (b'phone', b'Phone'), (b'meetingorevent', b'Meeting or Event'), (b'job', b'Job Followup'), (b'pssemail', b'Partner Saved Search Email')])),
                ('contact_email', models.CharField(max_length=255, verbose_name=b'Contact Email', blank=True)),
                ('contact_phone', models.CharField(default=b'', max_length=30, verbose_name=b'Contact Phone Number', blank=True)),
                ('location', models.CharField(default=b'', max_length=255, verbose_name=b'Meeting Location', blank=True)),
                ('length', models.TimeField(null=True, verbose_name=b'Meeting Length', blank=True)),
                ('subject', models.CharField(default=b'', max_length=255, verbose_name=b'Subject or Topic', blank=True)),
                ('date_time', models.DateTimeField(verbose_name=b'Date & Time', blank=True)),
                ('notes', models.TextField(default=b'', max_length=1000, verbose_name=b'Details, Notes or Transcripts', blank=True)),
                ('job_id', models.CharField(default=b'', max_length=40, verbose_name=b'Job Number/ID', blank=True)),
                ('job_applications', models.CharField(default=b'', max_length=6, verbose_name=b'Number of Applications', blank=True)),
                ('job_interviews', models.CharField(default=b'', max_length=6, verbose_name=b'Number of Interviews', blank=True)),
                ('job_hires', models.CharField(default=b'', max_length=6, verbose_name=b'Number of Hires', blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Location',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('label', models.CharField(max_length=60, verbose_name=b'Address Label', blank=True)),
                ('address_line_one', models.CharField(max_length=255, verbose_name=b'Address Line One', blank=True)),
                ('address_line_two', models.CharField(max_length=255, verbose_name=b'Address Line Two', blank=True)),
                ('city', models.CharField(max_length=255, verbose_name=b'City')),
                ('state', models.CharField(max_length=200, verbose_name=b'State/Region')),
                ('country_code', models.CharField(default=b'USA', max_length=3, verbose_name=b'Country')),
                ('postal_code', models.CharField(max_length=12, verbose_name=b'Postal Code', blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Partner',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255, verbose_name=b'Partner Organization')),
                ('data_source', models.CharField(max_length=255, verbose_name=b'Source', blank=True)),
                ('uri', models.URLField(verbose_name=b'URL', blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='PartnerLibrary',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('data_source', models.CharField(default=b'Employment Referral Resource Directory', max_length=255)),
                ('name', models.CharField(max_length=255, verbose_name=b'Partner Organization')),
                ('uri', models.URLField(blank=True)),
                ('region', models.CharField(max_length=30, blank=True)),
                ('state', models.CharField(max_length=30, blank=True)),
                ('area', models.CharField(max_length=255, blank=True)),
                ('contact_name', models.CharField(max_length=255, blank=True)),
                ('phone', models.CharField(max_length=30, blank=True)),
                ('phone_ext', models.CharField(max_length=10, blank=True)),
                ('alt_phone', models.CharField(max_length=30, blank=True)),
                ('fax', models.CharField(max_length=30, blank=True)),
                ('email', models.CharField(max_length=255, blank=True)),
                ('street1', models.CharField(max_length=255, blank=True)),
                ('street2', models.CharField(max_length=255, blank=True)),
                ('city', models.CharField(max_length=255, blank=True)),
                ('st', models.CharField(max_length=10, blank=True)),
                ('zip_code', models.CharField(max_length=12, blank=True)),
                ('is_minority', models.BooleanField(default=False, verbose_name=b'minority')),
                ('is_female', models.BooleanField(default=False, verbose_name=b'female')),
                ('is_disabled', models.BooleanField(default=False, verbose_name=b'disabled')),
                ('is_veteran', models.BooleanField(default=False, verbose_name=b'veteran')),
                ('is_disabled_veteran', models.BooleanField(default=False, verbose_name=b'disabled_veteran')),
            ],
        ),
        migrations.CreateModel(
            name='PRMAttachment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('attachment', models.FileField(max_length=767, null=True, upload_to=mypartners.models.get_file_name, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Status',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('code', models.PositiveSmallIntegerField(default=1, verbose_name=b'Status Code', choices=[(0, b'Unprocessed'), (1, b'Approved'), (2, b'Denied')])),
                ('last_modified', models.DateTimeField(auto_now=True, verbose_name=b'Last Modified')),
            ],
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('hex_color', models.CharField(default=b'd4d4d4', max_length=6, blank=True)),
                ('created_on', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'tag',
            },
        ),
    ]
