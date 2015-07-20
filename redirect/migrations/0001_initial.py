# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ATSSourceCode',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('buid', models.IntegerField(default=0)),
                ('ats_name', models.CharField(max_length=255)),
                ('parameter_name', models.CharField(max_length=255)),
                ('parameter_value', models.CharField(max_length=255)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CanonicalMicrosite',
            fields=[
                ('buid', models.IntegerField(default=0, serialize=False, primary_key=True)),
                ('canonical_microsite_url', models.URLField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CompanyEmail',
            fields=[
                ('buid', models.IntegerField(serialize=False, primary_key=True)),
                ('email', models.EmailField(max_length=75)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CustomExcludedViewSource',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('buid', models.IntegerField(help_text='Business unit id that wants a custom exclusion')),
                ('view_source', models.IntegerField(help_text='View source that should be excluded')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='DestinationManipulation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('action_type', models.IntegerField(help_text='Always 1 or 2')),
                ('buid', models.IntegerField(help_text='Business unit ID that owns this manipulation')),
                ('view_source', models.IntegerField(help_text='View source ID for aparticular manipulation')),
                ('action', models.CharField(default=b'sourcecodetag', choices=[(b'sourcecodetag', b'sourcecodetag'), (b'amptoamp', b'amptoamp'), (b'cframe', b'cframe'), (b'anchorredirectissue', b'anchorredirectissue'), (b'urlswap', b'urlswap'), (b'replacethenadd', b'replacethenadd'), (b'replacethenaddpre', b'replacethenaddpre'), (b'sourceurlwrapappend', b'sourceurlwrapappend'), (b'sourcecodeinsertion', b'sourcecodeinsertion'), (b'sourceurlwrapunencoded', b'sourceurlwrapunencoded'), (b'sourceurlwrapunencodedappend', b'sourceurlwrapunencodedappend'), (b'switchlastinstance', b'switchlastinstance'), (b'switchlastthenadd', b'switchlastthenadd'), (b'sourcecodeswitch', b'sourcecodeswitch'), (b'doubleclickunwind', b'doubleclickunwind'), (b'fixurl', b'fixurl')], max_length=255, blank=True, help_text='String describing what type of manipulation is to occur', null=True)),
                ('value_1', models.TextField(blank=True)),
                ('value_2', models.TextField(blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='EmailRedirectLog',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('from_addr', models.EmailField(max_length=75)),
                ('to_guid', models.CharField(max_length=38)),
                ('buid', models.IntegerField()),
                ('to_addr', models.EmailField(max_length=75)),
                ('sent', models.DateTimeField(auto_now_add=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ExcludedViewSource',
            fields=[
                ('view_source', models.IntegerField(help_text='This view source will not redirect to a microsite', serialize=False, primary_key=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Redirect',
            fields=[
                ('guid', models.CharField(help_text='42-character hex string', max_length=42, serialize=False, primary_key=True, db_index=True)),
                ('buid', models.IntegerField(default=0, help_text='Business unit ID for a given job provider')),
                ('uid', models.IntegerField(help_text="Unique id on partner's ATS or other job repository", unique=True, null=True, blank=True)),
                ('url', models.TextField(help_text='URL being manipulated')),
                ('new_date', models.DateTimeField(help_text='Date that this job was added')),
                ('expired_date', models.DateTimeField(help_text='Date that this job was marked as expired', null=True, db_index=True, blank=True)),
                ('job_location', models.CharField(max_length=255, blank=True)),
                ('job_title', models.CharField(max_length=255, blank=True)),
                ('company_name', models.TextField(blank=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='RedirectAction',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('buid', models.IntegerField(default=0)),
                ('action', models.IntegerField(default=0, choices=[(0, b'sourcecodetag'), (1, b'amptoamp'), (2, b'cframe'), (3, b'anchorredirectissue'), (4, b'urlswap'), (5, b'replacethenadd'), (6, b'replacethenaddpre'), (7, b'sourceurlwrapappend'), (8, b'sourcecodeinsertion'), (9, b'sourceurlwrapunencoded'), (10, b'sourceurlwrapunencodedappend'), (11, b'switchlastinstance'), (12, b'switchlastthenadd'), (13, b'sourcecodeswitch'), (14, b'doubleclickunwind'), (15, b'fixurl')])),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='RedirectArchive',
            fields=[
                ('guid', models.CharField(help_text='42-character hex string', max_length=42, serialize=False, primary_key=True, db_index=True)),
                ('buid', models.IntegerField(default=0, help_text='Business unit ID for a given job provider')),
                ('uid', models.IntegerField(help_text="Unique id on partner's ATS or other job repository", unique=True, null=True, blank=True)),
                ('url', models.TextField(help_text='URL being manipulated')),
                ('new_date', models.DateTimeField(help_text='Date that this job was added')),
                ('expired_date', models.DateTimeField(help_text='Date that this job was marked as expired', null=True, db_index=True, blank=True)),
                ('job_location', models.CharField(max_length=255, blank=True)),
                ('job_title', models.CharField(max_length=255, blank=True)),
                ('company_name', models.TextField(blank=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ViewSource',
            fields=[
                ('view_source_id', models.IntegerField(default=None, serialize=False, primary_key=True, blank=True)),
                ('name', models.CharField(max_length=255, blank=True)),
                ('friendly_name', models.CharField(max_length=255, blank=True)),
                ('microsite', models.BooleanField(default=False, help_text='Defunct; Use CanonicalMicrosite')),
                ('include_ga_params', models.BooleanField(default=False, help_text='Enables addition of Google Analytics parameters')),
                ('view_source_type', models.IntegerField(default=0)),
            ],
            options={
                'get_latest_by': 'view_source_id',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ViewSourceGroup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100, verbose_name='Name of this view source group')),
                ('view_source', models.ManyToManyField(to='redirect.ViewSource')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='redirectaction',
            name='view_source',
            field=models.ForeignKey(to='redirect.ViewSource'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='redirectaction',
            unique_together=set([('buid', 'view_source', 'action')]),
        ),
        migrations.AlterIndexTogether(
            name='redirectaction',
            index_together=set([('buid', 'view_source')]),
        ),
        migrations.AlterUniqueTogether(
            name='destinationmanipulation',
            unique_together=set([('action_type', 'buid', 'view_source')]),
        ),
        migrations.AlterUniqueTogether(
            name='customexcludedviewsource',
            unique_together=set([('buid', 'view_source')]),
        ),
        migrations.AlterIndexTogether(
            name='customexcludedviewsource',
            index_together=set([('buid', 'view_source')]),
        ),
        migrations.AddField(
            model_name='atssourcecode',
            name='view_source',
            field=models.ForeignKey(to='redirect.ViewSource', null=True),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='atssourcecode',
            unique_together=set([('ats_name', 'parameter_name', 'parameter_value', 'buid', 'view_source')]),
        ),
    ]
