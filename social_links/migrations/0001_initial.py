# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import social_links.models


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('auth', '0006_require_contenttypes_0002'),
        ('seo', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='MicrositeCarousel',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('is_active', models.BooleanField(default=False, verbose_name=b'Active')),
                ('include_all_sites', models.BooleanField(default=False, verbose_name=b"Include All Group's Sites")),
                ('display_rows', models.IntegerField(verbose_name=b'Display Rows', choices=[(1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6), (7, 7), (8, 8)])),
                ('carousel_title', models.CharField(max_length=200, null=True, verbose_name=b'Carousel Title', blank=True)),
                ('group', models.ForeignKey(to='auth.Group', null=True)),
                ('link_sites', models.ManyToManyField(related_name='linked_carousel', to='seo.SeoSite', blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='SocialLink',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('link_url', models.URLField()),
                ('link_title', models.CharField(max_length=60, db_index=True)),
                ('link_type', models.CharField(max_length=255, choices=[(b'company', b'Company'), (b'social', b'Social'), (b'directemployers', b'DirectEmployers')])),
                ('link_icon', models.CharField(default=b'default', max_length=255)),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType')),
                ('group', models.ForeignKey(to='auth.Group', null=True)),
                ('sites', models.ManyToManyField(to='seo.SeoSite')),
            ],
        ),
        migrations.CreateModel(
            name='SocialLinkType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('site', models.CharField(unique=True, max_length=60)),
                ('icon', models.FileField(max_length=767, upload_to=social_links.models.get_location)),
            ],
        ),
    ]
