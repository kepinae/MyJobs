# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Block',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('offset', models.PositiveIntegerField()),
                ('span', models.PositiveIntegerField()),
                ('template', models.TextField()),
                ('head', models.TextField(blank=True)),
                ('updated', models.DateTimeField(auto_now=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ApplyLinkBlock',
            fields=[
                ('block_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='myblocks.Block')),
            ],
            options={
            },
            bases=('myblocks.block',),
        ),
        migrations.CreateModel(
            name='BlockOrder',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('order', models.PositiveIntegerField()),
                ('updated', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ('order',),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='BreadboxBlock',
            fields=[
                ('block_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='myblocks.Block')),
            ],
            options={
            },
            bases=('myblocks.block',),
        ),
        migrations.CreateModel(
            name='ColumnBlock',
            fields=[
                ('block_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='myblocks.Block')),
            ],
            options={
            },
            bases=('myblocks.block',),
        ),
        migrations.CreateModel(
            name='ColumnBlockOrder',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('order', models.PositiveIntegerField()),
                ('updated', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ('order',),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ContentBlock',
            fields=[
                ('block_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='myblocks.Block')),
            ],
            options={
            },
            bases=('myblocks.block',),
        ),
        migrations.CreateModel(
            name='FacetBlurbBlock',
            fields=[
                ('block_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='myblocks.Block')),
            ],
            options={
            },
            bases=('myblocks.block',),
        ),
        migrations.CreateModel(
            name='JobDetailBlock',
            fields=[
                ('block_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='myblocks.Block')),
            ],
            options={
            },
            bases=('myblocks.block',),
        ),
        migrations.CreateModel(
            name='JobDetailBreadboxBlock',
            fields=[
                ('block_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='myblocks.Block')),
            ],
            options={
            },
            bases=('myblocks.block',),
        ),
        migrations.CreateModel(
            name='JobDetailHeaderBlock',
            fields=[
                ('block_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='myblocks.Block')),
            ],
            options={
            },
            bases=('myblocks.block',),
        ),
        migrations.CreateModel(
            name='LoginBlock',
            fields=[
                ('block_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='myblocks.Block')),
            ],
            options={
            },
            bases=('myblocks.block',),
        ),
        migrations.CreateModel(
            name='MoreButtonBlock',
            fields=[
                ('block_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='myblocks.Block')),
            ],
            options={
            },
            bases=('myblocks.block',),
        ),
        migrations.CreateModel(
            name='Page',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('page_type', models.CharField(max_length=255, choices=[(b'404', b'404'), (b'home_page', b'Home Page'), (b'job_detail', b'Job Detail Page'), (b'search_results', b'Job Search Results Page'), (b'login', b'Login Page'), (b'no_results', b'No Results Found')])),
                ('name', models.CharField(max_length=255)),
                ('status', models.CharField(default=b'production', max_length=255, choices=[(b'staging', b'Staging'), (b'production', b'Production')])),
                ('head', models.TextField(blank=True)),
                ('updated', models.DateTimeField(auto_now=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='RegistrationBlock',
            fields=[
                ('block_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='myblocks.Block')),
            ],
            options={
            },
            bases=('myblocks.block',),
        ),
        migrations.CreateModel(
            name='Row',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('updated', models.DateTimeField(auto_now=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='RowOrder',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('order', models.PositiveIntegerField()),
                ('updated', models.DateTimeField(auto_now=True)),
                ('page', models.ForeignKey(to='myblocks.Page')),
                ('row', models.ForeignKey(to='myblocks.Row')),
            ],
            options={
                'ordering': ('order',),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SavedSearchWidgetBlock',
            fields=[
                ('block_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='myblocks.Block')),
            ],
            options={
            },
            bases=('myblocks.block',),
        ),
        migrations.CreateModel(
            name='SearchBoxBlock',
            fields=[
                ('block_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='myblocks.Block')),
            ],
            options={
            },
            bases=('myblocks.block',),
        ),
        migrations.CreateModel(
            name='SearchFilterBlock',
            fields=[
                ('block_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='myblocks.Block')),
            ],
            options={
            },
            bases=('myblocks.block',),
        ),
        migrations.CreateModel(
            name='SearchResultBlock',
            fields=[
                ('block_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='myblocks.Block')),
            ],
            options={
            },
            bases=('myblocks.block',),
        ),
        migrations.CreateModel(
            name='SearchResultHeaderBlock',
            fields=[
                ('block_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='myblocks.Block')),
            ],
            options={
            },
            bases=('myblocks.block',),
        ),
        migrations.CreateModel(
            name='ShareBlock',
            fields=[
                ('block_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='myblocks.Block')),
            ],
            options={
            },
            bases=('myblocks.block',),
        ),
        migrations.CreateModel(
            name='VeteranSearchBox',
            fields=[
                ('block_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='myblocks.Block')),
            ],
            options={
            },
            bases=('myblocks.block',),
        ),
        migrations.AddField(
            model_name='row',
            name='blocks',
            field=models.ManyToManyField(to='myblocks.Block', through='myblocks.BlockOrder'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='page',
            name='rows',
            field=models.ManyToManyField(to='myblocks.Row', through='myblocks.RowOrder'),
            preserve_default=True,
        ),
    ]
