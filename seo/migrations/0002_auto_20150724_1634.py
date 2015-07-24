# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
from django.conf import settings
import taggit.managers


class Migration(migrations.Migration):

    dependencies = [
        ('taggit', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('social_links', '0001_initial'),
        ('auth', '0006_require_contenttypes_0002'),
        ('postajob', '0002_auto_20150724_1634'),
        ('seo', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='seosite',
            name='microsite_carousel',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, blank=True, to='social_links.MicrositeCarousel', null=True),
        ),
        migrations.AddField(
            model_name='seosite',
            name='site_package',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, to='postajob.SitePackage', null=True),
        ),
        migrations.AddField(
            model_name='seosite',
            name='site_tags',
            field=models.ManyToManyField(to='seo.SiteTag', blank=True),
        ),
        migrations.AddField(
            model_name='seosite',
            name='special_commitments',
            field=models.ManyToManyField(to='seo.SpecialCommitment', blank=True),
        ),
        migrations.AddField(
            model_name='seosite',
            name='view_sources',
            field=models.ForeignKey(blank=True, to='seo.ViewSource', null=True),
        ),
        migrations.AddField(
            model_name='googleanalyticscampaign',
            name='group',
            field=models.ForeignKey(to='auth.Group', null=True),
        ),
        migrations.AddField(
            model_name='googleanalytics',
            name='group',
            field=models.ForeignKey(to='auth.Group', null=True),
        ),
        migrations.AddField(
            model_name='featuredcompany',
            name='company',
            field=models.ForeignKey(to='seo.Company'),
        ),
        migrations.AddField(
            model_name='featuredcompany',
            name='seosite',
            field=models.ForeignKey(to='seo.SeoSite'),
        ),
        migrations.AddField(
            model_name='custompage',
            name='group',
            field=models.ForeignKey(blank=True, to='auth.Group', null=True),
        ),
        migrations.AddField(
            model_name='customfacet',
            name='business_units',
            field=models.ManyToManyField(to='seo.BusinessUnit', blank=True),
        ),
        migrations.AddField(
            model_name='customfacet',
            name='group',
            field=models.ForeignKey(blank=True, to='auth.Group', null=True),
        ),
        migrations.AddField(
            model_name='customfacet',
            name='keyword',
            field=taggit.managers.TaggableManager(to='taggit.Tag', through='taggit.TaggedItem', help_text='A comma-separated list of tags.', verbose_name='Tags'),
        ),
        migrations.AddField(
            model_name='configuration',
            name='group',
            field=models.ForeignKey(to='auth.Group', null=True),
        ),
        migrations.AddField(
            model_name='companyuser',
            name='company',
            field=models.ForeignKey(to='seo.Company'),
        ),
        migrations.AddField(
            model_name='companyuser',
            name='group',
            field=models.ManyToManyField(to='auth.Group', blank=True),
        ),
        migrations.AddField(
            model_name='companyuser',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='company',
            name='admins',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL, through='seo.CompanyUser'),
        ),
        migrations.AddField(
            model_name='company',
            name='job_source_ids',
            field=models.ManyToManyField(to='seo.BusinessUnit'),
        ),
        migrations.AddField(
            model_name='company',
            name='prm_saved_search_sites',
            field=models.ManyToManyField(to='seo.SeoSite', blank=True),
        ),
        migrations.AddField(
            model_name='company',
            name='site_package',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, to='postajob.SitePackage', null=True),
        ),
        migrations.AddField(
            model_name='city',
            name='nation',
            field=models.ForeignKey(to='seo.Country'),
        ),
        migrations.AddField(
            model_name='businessunit',
            name='site_packages',
            field=models.ManyToManyField(to='postajob.SitePackage', blank=True),
        ),
        migrations.AddField(
            model_name='billboardimage',
            name='group',
            field=models.ForeignKey(to='auth.Group', null=True),
        ),
        migrations.AddField(
            model_name='billboardhotspot',
            name='billboard_image',
            field=models.ForeignKey(to='seo.BillboardImage'),
        ),
        migrations.AddField(
            model_name='atssourcecode',
            name='group',
            field=models.ForeignKey(to='auth.Group', null=True),
        ),
        migrations.AlterUniqueTogether(
            name='state',
            unique_together=set([('name', 'nation')]),
        ),
        migrations.AlterUniqueTogether(
            name='seositeredirect',
            unique_together=set([('redirect_url', 'seosite')]),
        ),
        migrations.AlterUniqueTogether(
            name='companyuser',
            unique_together=set([('user', 'company')]),
        ),
        migrations.AlterUniqueTogether(
            name='company',
            unique_together=set([('name', 'user_created')]),
        ),
    ]
