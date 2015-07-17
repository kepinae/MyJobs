# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'CustomFacet'
        db.create_table(u'seo_customfacet', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('name_slug', self.gf('django.db.models.fields.SlugField')(max_length=100, null=True, blank=True)),
            ('date_created', self.gf('django.db.models.fields.DateField')(auto_now=True, blank=True)),
            ('querystring', self.gf('django.db.models.fields.CharField')(max_length=2000, null=True, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=800, null=True, blank=True)),
            ('url_slab', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('blurb', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('show_blurb', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('show_production', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.Group'], null=True, blank=True)),
            ('country', self.gf('django.db.models.fields.CharField')(max_length=800, null=True, blank=True)),
            ('state', self.gf('django.db.models.fields.CharField')(max_length=800, null=True, blank=True)),
            ('city', self.gf('django.db.models.fields.CharField')(max_length=800, null=True, blank=True)),
            ('company', self.gf('django.db.models.fields.CharField')(max_length=800, null=True, blank=True)),
            ('onet', self.gf('django.db.models.fields.CharField')(max_length=10, null=True, blank=True)),
            ('always_show', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('saved_querystring', self.gf('django.db.models.fields.CharField')(max_length=10000, blank=True)),
        ))
        db.send_create_signal(u'seo', ['CustomFacet'])

        # Adding M2M table for field business_units on 'CustomFacet'
        m2m_table_name = db.shorten_name(u'seo_customfacet_business_units')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('customfacet', models.ForeignKey(orm[u'seo.customfacet'], null=False)),
            ('businessunit', models.ForeignKey(orm[u'seo.businessunit'], null=False))
        ))
        db.create_unique(m2m_table_name, ['customfacet_id', 'businessunit_id'])

        # Adding model 'jobListing'
        db.create_table(u'seo_joblisting', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('city', self.gf('django.db.models.fields.CharField')(max_length=200, null=True, blank=True)),
            ('citySlug', self.gf('django.db.models.fields.SlugField')(max_length=50, null=True, blank=True)),
            ('country', self.gf('django.db.models.fields.CharField')(max_length=200, null=True, blank=True)),
            ('countrySlug', self.gf('django.db.models.fields.SlugField')(max_length=50, null=True, blank=True)),
            ('country_short', self.gf('django.db.models.fields.CharField')(db_index=True, max_length=3, null=True, blank=True)),
            ('date_new', self.gf('django.db.models.fields.DateTimeField')()),
            ('date_updated', self.gf('django.db.models.fields.DateTimeField')()),
            ('description', self.gf('django.db.models.fields.TextField')()),
            ('hitkey', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('link', self.gf('django.db.models.fields.URLField')(max_length=200)),
            ('location', self.gf('django.db.models.fields.CharField')(max_length=200, null=True, blank=True)),
            ('reqid', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True)),
            ('state', self.gf('django.db.models.fields.CharField')(max_length=200, null=True, blank=True)),
            ('stateSlug', self.gf('django.db.models.fields.SlugField')(max_length=50, null=True, blank=True)),
            ('state_short', self.gf('django.db.models.fields.CharField')(max_length=3, null=True, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('titleSlug', self.gf('django.db.models.fields.SlugField')(max_length=200, null=True, blank=True)),
            ('uid', self.gf('django.db.models.fields.IntegerField')(unique=True, db_index=True)),
            ('zipcode', self.gf('django.db.models.fields.CharField')(max_length=15, null=True, blank=True)),
        ))
        db.send_create_signal(u'seo', ['jobListing'])

        # Adding model 'SeoSite'
        db.create_table(u'seo_seosite', (
            (u'site_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['sites.Site'], unique=True, primary_key=True)),
            ('group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.Group'], null=True)),
            ('microsite_carousel', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['social_links.MicrositeCarousel'], null=True, on_delete=models.SET_NULL, blank=True)),
            ('site_title', self.gf('django.db.models.fields.CharField')(default='', max_length=200, blank=True)),
            ('site_heading', self.gf('django.db.models.fields.CharField')(default='', max_length=200, blank=True)),
            ('site_description', self.gf('django.db.models.fields.CharField')(default='', max_length=200, blank=True)),
            ('google_analytics_campaigns', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['seo.GoogleAnalyticsCampaign'], null=True, blank=True)),
            ('view_sources', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['seo.ViewSource'], null=True, blank=True)),
            ('site_package', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['postajob.SitePackage'], null=True, on_delete=models.SET_NULL)),
        ))
        db.send_create_signal(u'seo', ['SeoSite'])

        # Adding M2M table for field configurations on 'SeoSite'
        m2m_table_name = db.shorten_name(u'seo_seosite_configurations')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('seosite', models.ForeignKey(orm[u'seo.seosite'], null=False)),
            ('configuration', models.ForeignKey(orm[u'seo.configuration'], null=False))
        ))
        db.create_unique(m2m_table_name, ['seosite_id', 'configuration_id'])

        # Adding M2M table for field google_analytics on 'SeoSite'
        m2m_table_name = db.shorten_name(u'seo_seosite_google_analytics')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('seosite', models.ForeignKey(orm[u'seo.seosite'], null=False)),
            ('googleanalytics', models.ForeignKey(orm[u'seo.googleanalytics'], null=False))
        ))
        db.create_unique(m2m_table_name, ['seosite_id', 'googleanalytics_id'])

        # Adding M2M table for field business_units on 'SeoSite'
        m2m_table_name = db.shorten_name(u'seo_seosite_business_units')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('seosite', models.ForeignKey(orm[u'seo.seosite'], null=False)),
            ('businessunit', models.ForeignKey(orm[u'seo.businessunit'], null=False))
        ))
        db.create_unique(m2m_table_name, ['seosite_id', 'businessunit_id'])

        # Adding M2M table for field featured_companies on 'SeoSite'
        m2m_table_name = db.shorten_name(u'seo_seosite_featured_companies')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('seosite', models.ForeignKey(orm[u'seo.seosite'], null=False)),
            ('company', models.ForeignKey(orm[u'seo.company'], null=False))
        ))
        db.create_unique(m2m_table_name, ['seosite_id', 'company_id'])

        # Adding M2M table for field billboard_images on 'SeoSite'
        m2m_table_name = db.shorten_name(u'seo_seosite_billboard_images')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('seosite', models.ForeignKey(orm[u'seo.seosite'], null=False)),
            ('billboardimage', models.ForeignKey(orm[u'seo.billboardimage'], null=False))
        ))
        db.create_unique(m2m_table_name, ['seosite_id', 'billboardimage_id'])

        # Adding M2M table for field ats_source_codes on 'SeoSite'
        m2m_table_name = db.shorten_name(u'seo_seosite_ats_source_codes')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('seosite', models.ForeignKey(orm[u'seo.seosite'], null=False)),
            ('atssourcecode', models.ForeignKey(orm[u'seo.atssourcecode'], null=False))
        ))
        db.create_unique(m2m_table_name, ['seosite_id', 'atssourcecode_id'])

        # Adding M2M table for field special_commitments on 'SeoSite'
        m2m_table_name = db.shorten_name(u'seo_seosite_special_commitments')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('seosite', models.ForeignKey(orm[u'seo.seosite'], null=False)),
            ('specialcommitment', models.ForeignKey(orm[u'seo.specialcommitment'], null=False))
        ))
        db.create_unique(m2m_table_name, ['seosite_id', 'specialcommitment_id'])

        # Adding M2M table for field site_tags on 'SeoSite'
        m2m_table_name = db.shorten_name(u'seo_seosite_site_tags')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('seosite', models.ForeignKey(orm[u'seo.seosite'], null=False)),
            ('sitetag', models.ForeignKey(orm[u'seo.sitetag'], null=False))
        ))
        db.create_unique(m2m_table_name, ['seosite_id', 'sitetag_id'])

        # Adding model 'SeoSiteFacet'
        db.create_table(u'seo_seositefacet', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('seosite', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['seo.SeoSite'])),
            ('customfacet', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['seo.CustomFacet'])),
            ('facet_type', self.gf('django.db.models.fields.CharField')(default='STD', max_length=4, db_index=True)),
            ('boolean_operation', self.gf('django.db.models.fields.CharField')(default='or', max_length=3, db_index=True)),
        ))
        db.send_create_signal(u'seo', ['SeoSiteFacet'])

        # Adding model 'Company'
        db.create_table(u'seo_company', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=200)),
            ('company_slug', self.gf('django.db.models.fields.SlugField')(max_length=200, null=True, blank=True)),
            ('logo_url', self.gf('django.db.models.fields.URLField')(max_length=200, null=True, blank=True)),
            ('linkedin_id', self.gf('django.db.models.fields.CharField')(max_length=20, null=True, blank=True)),
            ('og_img', self.gf('django.db.models.fields.URLField')(max_length=200, null=True, blank=True)),
            ('canonical_microsite', self.gf('django.db.models.fields.URLField')(max_length=200, null=True, blank=True)),
            ('member', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('digital_strategies_customer', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('enhanced', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('site_package', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['postajob.SitePackage'], null=True, on_delete=models.SET_NULL)),
            ('prm_access', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('product_access', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('user_created', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal(u'seo', ['Company'])

        # Adding M2M table for field job_source_ids on 'Company'
        m2m_table_name = db.shorten_name(u'seo_company_job_source_ids')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('company', models.ForeignKey(orm[u'seo.company'], null=False)),
            ('businessunit', models.ForeignKey(orm[u'seo.businessunit'], null=False))
        ))
        db.create_unique(m2m_table_name, ['company_id', 'businessunit_id'])

        # Adding model 'FeaturedCompany'
        db.create_table(u'seo_featuredcompany', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('seosite', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['seo.SeoSite'])),
            ('company', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['seo.Company'])),
            ('is_featured', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal(u'seo', ['FeaturedCompany'])

        # Adding model 'SpecialCommitment'
        db.create_table(u'seo_specialcommitment', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('commit', self.gf('django.db.models.fields.CharField')(max_length=200)),
        ))
        db.send_create_signal(u'seo', ['SpecialCommitment'])

        # Adding model 'GoogleAnalyticsCampaign'
        db.create_table(u'seo_googleanalyticscampaign', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(default='', max_length=200)),
            ('group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.Group'], null=True)),
            ('campaign_source', self.gf('django.db.models.fields.CharField')(default='', max_length=200)),
            ('campaign_medium', self.gf('django.db.models.fields.CharField')(default='', max_length=200)),
            ('campaign_name', self.gf('django.db.models.fields.CharField')(default='', max_length=200)),
            ('campaign_term', self.gf('django.db.models.fields.CharField')(default='', max_length=200)),
            ('campaign_content', self.gf('django.db.models.fields.CharField')(default='', max_length=200)),
        ))
        db.send_create_signal(u'seo', ['GoogleAnalyticsCampaign'])

        # Adding model 'ATSSourceCode'
        db.create_table(u'seo_atssourcecode', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(default='', max_length=200)),
            ('value', self.gf('django.db.models.fields.CharField')(default='', max_length=200)),
            ('group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.Group'], null=True)),
            ('ats_name', self.gf('django.db.models.fields.CharField')(default='', max_length=200)),
        ))
        db.send_create_signal(u'seo', ['ATSSourceCode'])

        # Adding model 'ViewSource'
        db.create_table(u'seo_viewsource', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(default='', max_length=200)),
            ('view_source', self.gf('django.db.models.fields.IntegerField')(default='', max_length=20)),
        ))
        db.send_create_signal(u'seo', ['ViewSource'])

        # Adding model 'BillboardImage'
        db.create_table(u'seo_billboardimage', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.Group'], null=True)),
            ('image_url', self.gf('django.db.models.fields.URLField')(max_length=200)),
            ('copyright_info', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('source_url', self.gf('django.db.models.fields.URLField')(max_length=200)),
            ('logo_url', self.gf('django.db.models.fields.URLField')(max_length=200, null=True, blank=True)),
            ('sponsor_url', self.gf('django.db.models.fields.URLField')(max_length=200, null=True, blank=True)),
        ))
        db.send_create_signal(u'seo', ['BillboardImage'])

        # Adding model 'BillboardHotspot'
        db.create_table(u'seo_billboardhotspot', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('billboard_image', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['seo.BillboardImage'])),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('text', self.gf('django.db.models.fields.CharField')(max_length=140)),
            ('url', self.gf('django.db.models.fields.URLField')(max_length=200, null=True, blank=True)),
            ('display_url', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('offset_x', self.gf('django.db.models.fields.IntegerField')()),
            ('offset_y', self.gf('django.db.models.fields.IntegerField')()),
            ('primary_color', self.gf('django.db.models.fields.CharField')(default='5A6D81', max_length=6)),
            ('font_color', self.gf('django.db.models.fields.CharField')(default='FFFFFF', max_length=6)),
            ('border_color', self.gf('django.db.models.fields.CharField')(default='FFFFFF', max_length=6)),
        ))
        db.send_create_signal(u'seo', ['BillboardHotspot'])

        # Adding model 'SiteTag'
        db.create_table(u'seo_sitetag', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('site_tag', self.gf('django.db.models.fields.CharField')(unique=True, max_length=100)),
            ('tag_navigation', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal(u'seo', ['SiteTag'])

        # Adding model 'SeoSiteRedirect'
        db.create_table(u'seo_seositeredirect', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('redirect_url', self.gf('django.db.models.fields.CharField')(max_length=100, db_index=True)),
            ('seosite', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['seo.SeoSite'])),
        ))
        db.send_create_signal(u'seo', ['SeoSiteRedirect'])

        # Adding unique constraint on 'SeoSiteRedirect', fields ['redirect_url', 'seosite']
        db.create_unique(u'seo_seositeredirect', ['redirect_url', 'seosite_id'])

        # Adding model 'Configuration'
        db.create_table(u'seo_configuration', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=50, null=True)),
            ('status', self.gf('django.db.models.fields.IntegerField')(default=1, null=True, db_index=True, blank=True)),
            ('defaultBlurb', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('defaultBlurbTitle', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True)),
            ('browse_country_show', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('browse_state_show', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('browse_city_show', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('browse_title_show', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('browse_facet_show', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('browse_moc_show', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('browse_company_show', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('browse_country_text', self.gf('django.db.models.fields.CharField')(default='Country', max_length=50)),
            ('browse_state_text', self.gf('django.db.models.fields.CharField')(default='State', max_length=50)),
            ('browse_city_text', self.gf('django.db.models.fields.CharField')(default='City', max_length=50)),
            ('browse_title_text', self.gf('django.db.models.fields.CharField')(default='Title', max_length=50)),
            ('browse_facet_text', self.gf('django.db.models.fields.CharField')(default='Job Profiles', max_length=50)),
            ('browse_moc_text', self.gf('django.db.models.fields.CharField')(default='Military Titles', max_length=50)),
            ('browse_company_text', self.gf('django.db.models.fields.CharField')(default='Company', max_length=50)),
            ('browse_country_order', self.gf('django.db.models.fields.IntegerField')(default=3)),
            ('browse_state_order', self.gf('django.db.models.fields.IntegerField')(default=4)),
            ('browse_city_order', self.gf('django.db.models.fields.IntegerField')(default=5)),
            ('browse_title_order', self.gf('django.db.models.fields.IntegerField')(default=6)),
            ('browse_facet_order', self.gf('django.db.models.fields.IntegerField')(default=2)),
            ('browse_moc_order', self.gf('django.db.models.fields.IntegerField')(default=1)),
            ('browse_company_order', self.gf('django.db.models.fields.IntegerField')(default=7)),
            ('num_subnav_items_to_show', self.gf('django.db.models.fields.IntegerField')(default=9)),
            ('num_filter_items_to_show', self.gf('django.db.models.fields.IntegerField')(default=10)),
            ('num_job_items_to_show', self.gf('django.db.models.fields.IntegerField')(default=15)),
            ('location_tag', self.gf('django.db.models.fields.CharField')(default='jobs', max_length=50)),
            ('title_tag', self.gf('django.db.models.fields.CharField')(default='jobs-in', max_length=50)),
            ('facet_tag', self.gf('django.db.models.fields.CharField')(default='new-jobs', max_length=50)),
            ('moc_tag', self.gf('django.db.models.fields.CharField')(default='vet-jobs', max_length=50)),
            ('company_tag', self.gf('django.db.models.fields.CharField')(default='careers', max_length=50)),
            ('meta', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('wide_header', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('header', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('body', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('wide_footer', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('footer', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('view_all_jobs_detail', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('directemployers_link', self.gf('django.db.models.fields.URLField')(default='http://directemployers.org', max_length=200)),
            ('show_social_footer', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('css_body', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('useCssBody', self.gf('django.db.models.fields.BooleanField')()),
            ('backgroundColor', self.gf('django.db.models.fields.CharField')(max_length=6, null=True, blank=True)),
            ('fontColor', self.gf('django.db.models.fields.CharField')(default='666666', max_length=6)),
            ('primaryColor', self.gf('django.db.models.fields.CharField')(default='990000', max_length=6)),
            ('secondaryColor', self.gf('django.db.models.fields.CharField')(max_length=6, null=True, blank=True)),
            ('group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.Group'], null=True)),
            ('revision', self.gf('django.db.models.fields.IntegerField')(default=1)),
            ('home_page_template', self.gf('django.db.models.fields.CharField')(default='home_page/home_page_listing.html', max_length=200)),
            ('show_home_microsite_carousel', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('show_home_social_footer', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('publisher', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('percent_featured', self.gf('django.db.models.fields.DecimalField')(default='0.5', max_digits=3, decimal_places=2)),
            ('show_saved_search_widget', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal(u'seo', ['Configuration'])

        # Adding model 'GoogleAnalytics'
        db.create_table(u'seo_googleanalytics', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('web_property_id', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.Group'], null=True)),
        ))
        db.send_create_signal(u'seo', ['GoogleAnalytics'])

        # Adding model 'BusinessUnit'
        db.create_table(u'seo_businessunit', (
            ('id', self.gf('django.db.models.fields.IntegerField')(max_length=10, primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=500, null=True, blank=True)),
            ('title_slug', self.gf('django.db.models.fields.SlugField')(max_length=500, null=True, blank=True)),
            ('date_crawled', self.gf('django.db.models.fields.DateTimeField')()),
            ('date_updated', self.gf('django.db.models.fields.DateTimeField')()),
            ('associated_jobs', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('federal_contractor', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('enable_markdown', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal(u'seo', ['BusinessUnit'])

        # Adding model 'Country'
        db.create_table(u'seo_country', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255, db_index=True)),
            ('abbrev', self.gf('django.db.models.fields.CharField')(db_index=True, max_length=255, null=True, blank=True)),
            ('abbrev_short', self.gf('django.db.models.fields.CharField')(db_index=True, max_length=255, null=True, blank=True)),
        ))
        db.send_create_signal(u'seo', ['Country'])

        # Adding model 'State'
        db.create_table(u'seo_state', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255, db_index=True)),
            ('nation', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['seo.Country'])),
        ))
        db.send_create_signal(u'seo', ['State'])

        # Adding unique constraint on 'State', fields ['name', 'nation']
        db.create_unique(u'seo_state', ['name', 'nation_id'])

        # Adding model 'City'
        db.create_table(u'seo_city', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255, db_index=True)),
            ('nation', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['seo.Country'])),
        ))
        db.send_create_signal(u'seo', ['City'])

        # Adding model 'CustomPage'
        db.create_table(u'seo_custompage', (
            (u'flatpage_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['flatpages.FlatPage'], unique=True, primary_key=True)),
            ('group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.Group'], null=True, blank=True)),
        ))
        db.send_create_signal(u'seo', ['CustomPage'])

        # Adding model 'CompanyUser'
        db.create_table('mydashboard_companyuser', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['myjobs.User'])),
            ('company', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['seo.Company'])),
            ('date_added', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal(u'seo', ['CompanyUser'])

        # Adding unique constraint on 'CompanyUser', fields ['user', 'company']
        db.create_unique('mydashboard_companyuser', ['user_id', 'company_id'])

        # Adding M2M table for field group on 'CompanyUser'
        m2m_table_name = db.shorten_name('mydashboard_companyuser_group')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('companyuser', models.ForeignKey(orm[u'seo.companyuser'], null=False)),
            ('group', models.ForeignKey(orm[u'auth.group'], null=False))
        ))
        db.create_unique(m2m_table_name, ['companyuser_id', 'group_id'])


    def backwards(self, orm):
        # Removing unique constraint on 'CompanyUser', fields ['user', 'company']
        db.delete_unique('mydashboard_companyuser', ['user_id', 'company_id'])

        # Removing unique constraint on 'State', fields ['name', 'nation']
        db.delete_unique(u'seo_state', ['name', 'nation_id'])

        # Removing unique constraint on 'SeoSiteRedirect', fields ['redirect_url', 'seosite']
        db.delete_unique(u'seo_seositeredirect', ['redirect_url', 'seosite_id'])

        # Deleting model 'CustomFacet'
        db.delete_table(u'seo_customfacet')

        # Removing M2M table for field business_units on 'CustomFacet'
        db.delete_table(db.shorten_name(u'seo_customfacet_business_units'))

        # Deleting model 'jobListing'
        db.delete_table(u'seo_joblisting')

        # Deleting model 'SeoSite'
        db.delete_table(u'seo_seosite')

        # Removing M2M table for field configurations on 'SeoSite'
        db.delete_table(db.shorten_name(u'seo_seosite_configurations'))

        # Removing M2M table for field google_analytics on 'SeoSite'
        db.delete_table(db.shorten_name(u'seo_seosite_google_analytics'))

        # Removing M2M table for field business_units on 'SeoSite'
        db.delete_table(db.shorten_name(u'seo_seosite_business_units'))

        # Removing M2M table for field featured_companies on 'SeoSite'
        db.delete_table(db.shorten_name(u'seo_seosite_featured_companies'))

        # Removing M2M table for field billboard_images on 'SeoSite'
        db.delete_table(db.shorten_name(u'seo_seosite_billboard_images'))

        # Removing M2M table for field ats_source_codes on 'SeoSite'
        db.delete_table(db.shorten_name(u'seo_seosite_ats_source_codes'))

        # Removing M2M table for field special_commitments on 'SeoSite'
        db.delete_table(db.shorten_name(u'seo_seosite_special_commitments'))

        # Removing M2M table for field site_tags on 'SeoSite'
        db.delete_table(db.shorten_name(u'seo_seosite_site_tags'))

        # Deleting model 'SeoSiteFacet'
        db.delete_table(u'seo_seositefacet')

        # Deleting model 'Company'
        db.delete_table(u'seo_company')

        # Removing M2M table for field job_source_ids on 'Company'
        db.delete_table(db.shorten_name(u'seo_company_job_source_ids'))

        # Deleting model 'FeaturedCompany'
        db.delete_table(u'seo_featuredcompany')

        # Deleting model 'SpecialCommitment'
        db.delete_table(u'seo_specialcommitment')

        # Deleting model 'GoogleAnalyticsCampaign'
        db.delete_table(u'seo_googleanalyticscampaign')

        # Deleting model 'ATSSourceCode'
        db.delete_table(u'seo_atssourcecode')

        # Deleting model 'ViewSource'
        db.delete_table(u'seo_viewsource')

        # Deleting model 'BillboardImage'
        db.delete_table(u'seo_billboardimage')

        # Deleting model 'BillboardHotspot'
        db.delete_table(u'seo_billboardhotspot')

        # Deleting model 'SiteTag'
        db.delete_table(u'seo_sitetag')

        # Deleting model 'SeoSiteRedirect'
        db.delete_table(u'seo_seositeredirect')

        # Deleting model 'Configuration'
        db.delete_table(u'seo_configuration')

        # Deleting model 'GoogleAnalytics'
        db.delete_table(u'seo_googleanalytics')

        # Deleting model 'BusinessUnit'
        db.delete_table(u'seo_businessunit')

        # Deleting model 'Country'
        db.delete_table(u'seo_country')

        # Deleting model 'State'
        db.delete_table(u'seo_state')

        # Deleting model 'City'
        db.delete_table(u'seo_city')

        # Deleting model 'CustomPage'
        db.delete_table(u'seo_custompage')

        # Deleting model 'CompanyUser'
        db.delete_table('mydashboard_companyuser')

        # Removing M2M table for field group on 'CompanyUser'
        db.delete_table(db.shorten_name('mydashboard_companyuser_group'))


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'flatpages.flatpage': {
            'Meta': {'ordering': "(u'url',)", 'object_name': 'FlatPage', 'db_table': "u'django_flatpage'"},
            'content': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'enable_comments': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'registration_required': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'sites': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['sites.Site']", 'symmetrical': 'False'}),
            'template_name': ('django.db.models.fields.CharField', [], {'max_length': '70', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '100', 'db_index': 'True'})
        },
        u'myjobs.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'deactivate_type': ('django.db.models.fields.CharField', [], {'default': "'none'", 'max_length': '11'}),
            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '255', 'db_index': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'gravatar': ('django.db.models.fields.EmailField', [], {'db_index': 'True', 'max_length': '255', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_disabled': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_verified': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'last_response': ('django.db.models.fields.DateField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'opt_in_employers': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'opt_in_myjobs': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'password_change': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'profile_completion': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'source': ('django.db.models.fields.CharField', [], {'default': "'https://secure.my.jobs'", 'max_length': '255'}),
            'timezone': ('django.db.models.fields.CharField', [], {'default': "'America/New_York'", 'max_length': '255'}),
            'user_guid': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100', 'db_index': 'True'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Permission']"})
        },
        u'postajob.package': {
            'Meta': {'object_name': 'Package'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        u'postajob.sitepackage': {
            'Meta': {'object_name': 'SitePackage', '_ormbases': [u'postajob.Package']},
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['seo.Company']", 'null': 'True', 'blank': 'True'}),
            u'package_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['postajob.Package']", 'unique': 'True', 'primary_key': 'True'}),
            'sites': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['seo.SeoSite']", 'null': 'True', 'symmetrical': 'False'})
        },
        u'seo.atssourcecode': {
            'Meta': {'object_name': 'ATSSourceCode'},
            'ats_name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.Group']", 'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200'}),
            'value': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200'})
        },
        u'seo.billboardhotspot': {
            'Meta': {'object_name': 'BillboardHotspot'},
            'billboard_image': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['seo.BillboardImage']"}),
            'border_color': ('django.db.models.fields.CharField', [], {'default': "'FFFFFF'", 'max_length': '6'}),
            'display_url': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'font_color': ('django.db.models.fields.CharField', [], {'default': "'FFFFFF'", 'max_length': '6'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'offset_x': ('django.db.models.fields.IntegerField', [], {}),
            'offset_y': ('django.db.models.fields.IntegerField', [], {}),
            'primary_color': ('django.db.models.fields.CharField', [], {'default': "'5A6D81'", 'max_length': '6'}),
            'text': ('django.db.models.fields.CharField', [], {'max_length': '140'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'})
        },
        u'seo.billboardimage': {
            'Meta': {'object_name': 'BillboardImage'},
            'copyright_info': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.Group']", 'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image_url': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'logo_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'source_url': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'sponsor_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        u'seo.businessunit': {
            'Meta': {'object_name': 'BusinessUnit'},
            'associated_jobs': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'date_crawled': ('django.db.models.fields.DateTimeField', [], {}),
            'date_updated': ('django.db.models.fields.DateTimeField', [], {}),
            'enable_markdown': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'federal_contractor': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.IntegerField', [], {'max_length': '10', 'primary_key': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '500', 'null': 'True', 'blank': 'True'}),
            'title_slug': ('django.db.models.fields.SlugField', [], {'max_length': '500', 'null': 'True', 'blank': 'True'})
        },
        u'seo.city': {
            'Meta': {'object_name': 'City'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'nation': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['seo.Country']"})
        },
        u'seo.company': {
            'Meta': {'ordering': "['name']", 'object_name': 'Company'},
            'admins': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['myjobs.User']", 'through': u"orm['seo.CompanyUser']", 'symmetrical': 'False'}),
            'canonical_microsite': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'company_slug': ('django.db.models.fields.SlugField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'digital_strategies_customer': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'enhanced': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'job_source_ids': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['seo.BusinessUnit']", 'symmetrical': 'False'}),
            'linkedin_id': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'logo_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'member': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'}),
            'og_img': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'prm_access': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'product_access': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'site_package': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['postajob.SitePackage']", 'null': 'True', 'on_delete': 'models.SET_NULL'}),
            'user_created': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        u'seo.companyuser': {
            'Meta': {'unique_together': "(('user', 'company'),)", 'object_name': 'CompanyUser', 'db_table': "'mydashboard_companyuser'"},
            'company': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['seo.Company']"}),
            'date_added': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'group': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['myjobs.User']"})
        },
        u'seo.configuration': {
            'Meta': {'object_name': 'Configuration'},
            'backgroundColor': ('django.db.models.fields.CharField', [], {'max_length': '6', 'null': 'True', 'blank': 'True'}),
            'body': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'browse_city_order': ('django.db.models.fields.IntegerField', [], {'default': '5'}),
            'browse_city_show': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'browse_city_text': ('django.db.models.fields.CharField', [], {'default': "'City'", 'max_length': '50'}),
            'browse_company_order': ('django.db.models.fields.IntegerField', [], {'default': '7'}),
            'browse_company_show': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'browse_company_text': ('django.db.models.fields.CharField', [], {'default': "'Company'", 'max_length': '50'}),
            'browse_country_order': ('django.db.models.fields.IntegerField', [], {'default': '3'}),
            'browse_country_show': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'browse_country_text': ('django.db.models.fields.CharField', [], {'default': "'Country'", 'max_length': '50'}),
            'browse_facet_order': ('django.db.models.fields.IntegerField', [], {'default': '2'}),
            'browse_facet_show': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'browse_facet_text': ('django.db.models.fields.CharField', [], {'default': "'Job Profiles'", 'max_length': '50'}),
            'browse_moc_order': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'browse_moc_show': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'browse_moc_text': ('django.db.models.fields.CharField', [], {'default': "'Military Titles'", 'max_length': '50'}),
            'browse_state_order': ('django.db.models.fields.IntegerField', [], {'default': '4'}),
            'browse_state_show': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'browse_state_text': ('django.db.models.fields.CharField', [], {'default': "'State'", 'max_length': '50'}),
            'browse_title_order': ('django.db.models.fields.IntegerField', [], {'default': '6'}),
            'browse_title_show': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'browse_title_text': ('django.db.models.fields.CharField', [], {'default': "'Title'", 'max_length': '50'}),
            'company_tag': ('django.db.models.fields.CharField', [], {'default': "'careers'", 'max_length': '50'}),
            'css_body': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'defaultBlurb': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'defaultBlurbTitle': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'directemployers_link': ('django.db.models.fields.URLField', [], {'default': "'http://directemployers.org'", 'max_length': '200'}),
            'facet_tag': ('django.db.models.fields.CharField', [], {'default': "'new-jobs'", 'max_length': '50'}),
            'fontColor': ('django.db.models.fields.CharField', [], {'default': "'666666'", 'max_length': '6'}),
            'footer': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.Group']", 'null': 'True'}),
            'header': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'home_page_template': ('django.db.models.fields.CharField', [], {'default': "'home_page/home_page_listing.html'", 'max_length': '200'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location_tag': ('django.db.models.fields.CharField', [], {'default': "'jobs'", 'max_length': '50'}),
            'meta': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'moc_tag': ('django.db.models.fields.CharField', [], {'default': "'vet-jobs'", 'max_length': '50'}),
            'num_filter_items_to_show': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'num_job_items_to_show': ('django.db.models.fields.IntegerField', [], {'default': '15'}),
            'num_subnav_items_to_show': ('django.db.models.fields.IntegerField', [], {'default': '9'}),
            'percent_featured': ('django.db.models.fields.DecimalField', [], {'default': "'0.5'", 'max_digits': '3', 'decimal_places': '2'}),
            'primaryColor': ('django.db.models.fields.CharField', [], {'default': "'990000'", 'max_length': '6'}),
            'publisher': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'revision': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'secondaryColor': ('django.db.models.fields.CharField', [], {'max_length': '6', 'null': 'True', 'blank': 'True'}),
            'show_home_microsite_carousel': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'show_home_social_footer': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'show_saved_search_widget': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'show_social_footer': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '1', 'null': 'True', 'db_index': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True'}),
            'title_tag': ('django.db.models.fields.CharField', [], {'default': "'jobs-in'", 'max_length': '50'}),
            'useCssBody': ('django.db.models.fields.BooleanField', [], {}),
            'view_all_jobs_detail': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'wide_footer': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'wide_header': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'})
        },
        u'seo.country': {
            'Meta': {'object_name': 'Country'},
            'abbrev': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'abbrev_short': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'})
        },
        u'seo.customfacet': {
            'Meta': {'object_name': 'CustomFacet'},
            'always_show': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'blurb': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'business_units': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['seo.BusinessUnit']", 'null': 'True', 'blank': 'True'}),
            'city': ('django.db.models.fields.CharField', [], {'max_length': '800', 'null': 'True', 'blank': 'True'}),
            'company': ('django.db.models.fields.CharField', [], {'max_length': '800', 'null': 'True', 'blank': 'True'}),
            'country': ('django.db.models.fields.CharField', [], {'max_length': '800', 'null': 'True', 'blank': 'True'}),
            'date_created': ('django.db.models.fields.DateField', [], {'auto_now': 'True', 'blank': 'True'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.Group']", 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name_slug': ('django.db.models.fields.SlugField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'onet': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            'querystring': ('django.db.models.fields.CharField', [], {'max_length': '2000', 'null': 'True', 'blank': 'True'}),
            'saved_querystring': ('django.db.models.fields.CharField', [], {'max_length': '10000', 'blank': 'True'}),
            'show_blurb': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'show_production': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '800', 'null': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '800', 'null': 'True', 'blank': 'True'}),
            'url_slab': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'})
        },
        u'seo.custompage': {
            'Meta': {'ordering': "(u'url',)", 'object_name': 'CustomPage', '_ormbases': [u'flatpages.FlatPage']},
            u'flatpage_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['flatpages.FlatPage']", 'unique': 'True', 'primary_key': 'True'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.Group']", 'null': 'True', 'blank': 'True'})
        },
        u'seo.featuredcompany': {
            'Meta': {'object_name': 'FeaturedCompany'},
            'company': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['seo.Company']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_featured': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'seosite': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['seo.SeoSite']"})
        },
        u'seo.googleanalytics': {
            'Meta': {'object_name': 'GoogleAnalytics'},
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.Group']", 'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'web_property_id': ('django.db.models.fields.CharField', [], {'max_length': '20'})
        },
        u'seo.googleanalyticscampaign': {
            'Meta': {'object_name': 'GoogleAnalyticsCampaign'},
            'campaign_content': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200'}),
            'campaign_medium': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200'}),
            'campaign_name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200'}),
            'campaign_source': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200'}),
            'campaign_term': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.Group']", 'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200'})
        },
        u'seo.joblisting': {
            'Meta': {'object_name': 'jobListing'},
            'city': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'citySlug': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'country': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'countrySlug': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'country_short': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '3', 'null': 'True', 'blank': 'True'}),
            'date_new': ('django.db.models.fields.DateTimeField', [], {}),
            'date_updated': ('django.db.models.fields.DateTimeField', [], {}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'hitkey': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'link': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'location': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'reqid': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'stateSlug': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'state_short': ('django.db.models.fields.CharField', [], {'max_length': '3', 'null': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'titleSlug': ('django.db.models.fields.SlugField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'uid': ('django.db.models.fields.IntegerField', [], {'unique': 'True', 'db_index': 'True'}),
            'zipcode': ('django.db.models.fields.CharField', [], {'max_length': '15', 'null': 'True', 'blank': 'True'})
        },
        u'seo.seosite': {
            'Meta': {'ordering': "(u'domain',)", 'object_name': 'SeoSite', '_ormbases': [u'sites.Site']},
            'ats_source_codes': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['seo.ATSSourceCode']", 'null': 'True', 'blank': 'True'}),
            'billboard_images': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['seo.BillboardImage']", 'null': 'True', 'blank': 'True'}),
            'business_units': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['seo.BusinessUnit']", 'null': 'True', 'blank': 'True'}),
            'configurations': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['seo.Configuration']", 'symmetrical': 'False', 'blank': 'True'}),
            'facets': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['seo.CustomFacet']", 'null': 'True', 'through': u"orm['seo.SeoSiteFacet']", 'blank': 'True'}),
            'featured_companies': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['seo.Company']", 'null': 'True', 'blank': 'True'}),
            'google_analytics': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['seo.GoogleAnalytics']", 'null': 'True', 'blank': 'True'}),
            'google_analytics_campaigns': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['seo.GoogleAnalyticsCampaign']", 'null': 'True', 'blank': 'True'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.Group']", 'null': 'True'}),
            'microsite_carousel': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['social_links.MicrositeCarousel']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'site_description': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'site_heading': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'site_package': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['postajob.SitePackage']", 'null': 'True', 'on_delete': 'models.SET_NULL'}),
            u'site_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['sites.Site']", 'unique': 'True', 'primary_key': 'True'}),
            'site_tags': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['seo.SiteTag']", 'null': 'True', 'blank': 'True'}),
            'site_title': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'special_commitments': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['seo.SpecialCommitment']", 'null': 'True', 'blank': 'True'}),
            'view_sources': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['seo.ViewSource']", 'null': 'True', 'blank': 'True'})
        },
        u'seo.seositefacet': {
            'Meta': {'object_name': 'SeoSiteFacet'},
            'boolean_operation': ('django.db.models.fields.CharField', [], {'default': "'or'", 'max_length': '3', 'db_index': 'True'}),
            'customfacet': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['seo.CustomFacet']"}),
            'facet_type': ('django.db.models.fields.CharField', [], {'default': "'STD'", 'max_length': '4', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'seosite': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['seo.SeoSite']"})
        },
        u'seo.seositeredirect': {
            'Meta': {'unique_together': "(['redirect_url', 'seosite'],)", 'object_name': 'SeoSiteRedirect'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'redirect_url': ('django.db.models.fields.CharField', [], {'max_length': '100', 'db_index': 'True'}),
            'seosite': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['seo.SeoSite']"})
        },
        u'seo.sitetag': {
            'Meta': {'object_name': 'SiteTag'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'site_tag': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'tag_navigation': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        u'seo.specialcommitment': {
            'Meta': {'object_name': 'SpecialCommitment'},
            'commit': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        u'seo.state': {
            'Meta': {'unique_together': "(('name', 'nation'),)", 'object_name': 'State'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'nation': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['seo.Country']"})
        },
        u'seo.viewsource': {
            'Meta': {'object_name': 'ViewSource'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200'}),
            'view_source': ('django.db.models.fields.IntegerField', [], {'default': "''", 'max_length': '20'})
        },
        u'sites.site': {
            'Meta': {'ordering': "(u'domain',)", 'object_name': 'Site', 'db_table': "u'django_site'"},
            'domain': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'social_links.micrositecarousel': {
            'Meta': {'object_name': 'MicrositeCarousel'},
            'carousel_title': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'display_rows': ('django.db.models.fields.IntegerField', [], {}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.Group']", 'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'include_all_sites': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'link_sites': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'linked_carousel'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['seo.SeoSite']"})
        }
    }

    complete_apps = ['seo']