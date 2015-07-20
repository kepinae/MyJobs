# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('myblocks', '0001_initial'),
        ('contenttypes', '0001_initial'),
        ('seo', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='page',
            name='sites',
            field=models.ManyToManyField(to='seo.SeoSite'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='columnblockorder',
            name='block',
            field=models.ForeignKey(to='myblocks.Block'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='columnblockorder',
            name='column_block',
            field=models.ForeignKey(related_name='included_column_blocks', to='myblocks.ColumnBlock'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='columnblock',
            name='blocks',
            field=models.ManyToManyField(related_name='included_blocks', through='myblocks.ColumnBlockOrder', to='myblocks.Block'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='blockorder',
            name='block',
            field=models.ForeignKey(to='myblocks.Block'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='blockorder',
            name='row',
            field=models.ForeignKey(to='myblocks.Row'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='block',
            name='content_type',
            field=models.ForeignKey(editable=False, to='contenttypes.ContentType'),
            preserve_default=True,
        ),
    ]
