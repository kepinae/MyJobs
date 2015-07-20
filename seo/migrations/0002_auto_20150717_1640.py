# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
from django.conf import settings
import taggit.managers


class Migration(migrations.Migration):

    dependencies = [
        ('taggit', '0002_auto_20150717_0952'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('social_links', '0001_initial'),
        ('postajob', '0002_auto_20150717_1640'),
        ('auth', '0001_initial'),
        ('seo', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='seosite',
            name='microsite_carousel',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, blank=True, to='social_links.MicrositeCarousel', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='seosite',
            name='site_package',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, to='postajob.SitePackage', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='seosite',
            name='site_tags',
            field=models.ManyToManyField(to='seo.SiteTag', null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='seosite',
            name='special_commitments',
            field=models.ManyToManyField(to='seo.SpecialCommitment', null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='seosite',
            name='view_sources',
            field=models.ForeignKey(blank=True, to='seo.ViewSource', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='googleanalyticscampaign',
            name='group',
            field=models.ForeignKey(to='auth.Group', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='googleanalytics',
            name='group',
            field=models.ForeignKey(to='auth.Group', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='featuredcompany',
            name='company',
            field=models.ForeignKey(to='seo.Company'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='featuredcompany',
            name='seosite',
            field=models.ForeignKey(to='seo.SeoSite'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='custompage',
            name='group',
            field=models.ForeignKey(blank=True, to='auth.Group', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='customfacet',
            name='business_units',
            field=models.ManyToManyField(to='seo.BusinessUnit', null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='customfacet',
            name='group',
            field=models.ForeignKey(blank=True, to='auth.Group', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='customfacet',
            name='keyword',
            field=taggit.managers.TaggableManager(to='taggit.Tag', through='taggit.TaggedItem', help_text='A comma-separated list of tags.', verbose_name='Tags'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='configuration',
            name='group',
            field=models.ForeignKey(to='auth.Group', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='companyuser',
            name='company',
            field=models.ForeignKey(to='seo.Company'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='companyuser',
            name='group',
            field=models.ManyToManyField(to='auth.Group', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='companyuser',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='companyuser',
            unique_together=set([('user', 'company')]),
        ),
        migrations.AddField(
            model_name='company',
            name='admins',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL, through='seo.CompanyUser'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='company',
            name='job_source_ids',
            field=models.ManyToManyField(to='seo.BusinessUnit'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='company',
            name='prm_saved_search_sites',
            field=models.ManyToManyField(to='seo.SeoSite', null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='company',
            name='site_package',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, to='postajob.SitePackage', null=True),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='company',
            unique_together=set([('name', 'user_created')]),
        ),
        migrations.AddField(
            model_name='city',
            name='nation',
            field=models.ForeignKey(to='seo.Country'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='businessunit',
            name='site_packages',
            field=models.ManyToManyField(to='postajob.SitePackage', null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='billboardimage',
            name='group',
            field=models.ForeignKey(to='auth.Group', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='billboardhotspot',
            name='billboard_image',
            field=models.ForeignKey(to='seo.BillboardImage'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='atssourcecode',
            name='group',
            field=models.ForeignKey(to='auth.Group', null=True),
            preserve_default=True,
        ),
    ]
