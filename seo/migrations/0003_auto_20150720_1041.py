# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.contrib.contenttypes.management import update_all_contenttypes

def create_initial_data(apps, schema_editor):
    # create initial auth groups
    Group = apps.get_model('auth', 'group') 
    groups = [
        Group(name='Job Seeker'),
        Group(name='Employer'),
        Group(name='Partner'),
        Group(name='Staff'),
        Group(pk=9999999, name='SEO Test Group')
    ]

    Group.objects.bulk_create(groups)

    # create initial site
    Site = apps.get_model('sites', 'site')
    Site.objects.create(name='Default', domain='www.my.jobs')

    #create initial configurations
    Configuration = apps.get_model('seo', 'configuration')
    configurations = [
        Configuration(
            defaultBlurbTitle="",
            browse_facet_show=False,
            browse_country_show=False,
            header="",
            directemployers_link="http://directemployers.org/",
            meta="<link rel=\"stylesheet\" type=\"text/css\" href=\"//dn9tckvz2rpxv.cloudfront.net/css/default_config.css\" />\r\n<script type=\"text/javascript\" src=\"//dn9tckvz2rpxv.cloudfront.net/jobs.directemployers.org/cufon.js\"></script>\r\n\t\t<script type=\"text/javascript\" src=\"//dn9tckvz2rpxv.cloudfront.net/jobs.directemployers.org/Univers_LT_Std_400.font.js\"></script>\r\n\t\t<script type=\"text/javascript\">\r\n\t\t\tCufon.replace('h2,h4,table');\r\n\t\t</script>",
            fontColor="666666",
            title_tag="jobs-in",
            browse_facet_order=5,
            browse_country_text="Country",
            group=groups[-1],
            title="Default",
            wide_header="",
            browse_title_order=4,
            browse_title_text="Title",
            backgroundColor="ffffff",
            wide_footer="",
            status=1,
            num_subnav_items_to_show=20,
            browse_city_order=3,
            browse_state_order=2,
            browse_city_show=False,
            browse_state_show=False,
            browse_facet_text="Job Profiles",
            num_job_items_to_show=10,
            primaryColor="990000",
            facet_tag="new-jobs",
            browse_title_show=False,
            defaultBlurb="",
            location_tag="jobs",
            footer="<div id=\"mainContent\">\r\n\t\t\t<div id=\"SEOheader\">\r\n\t\t\t\t<img src=\"//dn9tckvz2rpxv.cloudfront.net/jobs.directemployers.org/images/DE_logo.png\" alt=\"\" />\r\n\t\t\t</div>\r\n\t\t\t<div id=\"SEOcontent\">\r\n\t\t\t\t<div id=\"contentHeader\">\r\n\t\t\t\t\t<h2>Dot Jobs Microsites and Direct SEO V3</h2>\r\n\t\t\t\t</div>\r\n\t\t\t\t<div id=\"contentContents\">\r\n\t\t\t\t\t<h4>CNAME Setup</h4>\r\n\t\t\t\t\t<p style=\"margin-top: 15px;\">\r\n\t\t\t\t\t\tAn alias, or canonical name, abbreviated CNAME, should be added to the Domain Name Server (DNS) file for your root domain<br />\r\n\t\t\t\t\t\t<span style=\"font-size: 11px;\">(Example: <span style=\"font-weight: bold; color: #990000;\">domain.jobs</span> or <span style=\"font-weight: bold; color: #990000;\">domain.com</span>).</span>\r\n\t\t\t\t\t</p>\r\n\t\t\t\t\t<p>\r\n\t\t\t\t\t\tHere is an example DNS entry for adding the subdomain <span style=\"font-weight: bold; color: #990000;\">jobs</span>.\r\n\t\t\t\t\t</p>\r\n\t\t\t\t\t<table id=\"first\">\r\n\t\t\t\t\t\t<tr>\r\n\t\t\t\t\t\t\t<td>jobs.domain.com.</td>\r\n\t\t\t\t\t\t\t<td>IN CNAME</td>\r\n\t\t\t\t\t\t\t<td>jobs.directemployers.org.</td>\r\n\t\t\t\t\t\t</tr>\r\n\t\t\t\t\t</table>\r\n\t\t\t\t\t<p style=\"font-size: 11px; margin-top: 15px;\">\r\n\t\t\t\t\t\t<span style=\"font-weight: bold;\">Note:</span><span style=\"font-style: italic;\"> The trailing periods may or may not be required, depending on your DNS server software</span>\r\n\t\t\t\t\t</p>\r\n\t\t\t\t\t<p style=\"margin-top: 15px;\">\r\n\t\t\t\t\t\tThe above line tells a web browser to get the IP address for <span style=\"font-weight: bold; color: #990000;\">jobs.domain.com</span> from the <span style=\"font-weight: bold; color: #990000;\">jobs.directemployers.org</span> DNS record. This alias allows DirectEmployers to host your SEO microsite, and is a standard method for companies to host third-party services - like blogs and RSS feeds - using their branded domain. \r\n\t\t\t\t\t</p>\r\n\t\t\t\t\t<p style=\"margin-top: 15px;\">\r\n\t\t\t\t\t\tYour company has the ultimate ownership and control over where your <span style=\"font-weight: bold; color: #990000;\">jobs.domain.com</span> hostname points, since your network administrator can change this DNS record at anytime to point to another service provider or internal server. Using a hostname based on your root domain should generate the fastest SEO ranking growth, and endear trust to the end-user who sees the hostname on a search engine results page.\r\n\t\t\t\t\t</p>\r\n\t\t\t\t\t<p style=\"margin-top: 15px;\">\r\n\t\t\t\t\t\tIf the jobs subdomain is already in use, then think about using another popular search phrase, like <span style=\"font-weight: bold; color: #990000;\">jobsearch</span>.<br />\r\n\t\t\t\t\t</p>\r\n\t\t\t\t\t<table id=\"second\">\r\n\t\t\t\t\t\t<tr>\r\n\t\t\t\t\t\t\t<td>jobsearch.domain.com.</td>\r\n\t\t\t\t\t\t\t<td>IN CNAME</td>\r\n\t\t\t\t\t\t\t<td>jobs.directemployers.org.</td>\r\n\t\t\t\t\t\t</tr>\r\n\t\t\t\t\t</table>\r\n\t\t\t\t\t<p style=\"margin-top: 15px;\">\r\n\t\t\t\t\t\tIf your company owns a .jobs top-level domain (TLD), then think about using this domain for hosting your SEO microsite. In this case, both subdomain and root domain CNAME entries are required. Here is an example DNS entry with <span style=\"font-weight: bold; color: #990000;\">www</span> as the subdomain and <span style=\"font-weight: bold; color: #990000;\">domain.jobs</span> as the root domain.\r\n\t\t\t\t\t</p>\r\n\t\t\t\t\t<table id=\"third\">\r\n\t\t\t\t\t\t<tr>\r\n\t\t\t\t\t\t\t<td>www.domain.jobs.</td>\r\n\t\t\t\t\t\t\t<td>IN CNAME</td>\r\n\t\t\t\t\t\t\t<td>jobs.directemployers.org.</td>\r\n\t\t\t\t\t\t</tr>\r\n\t\t\t\t\t\t<tr>\r\n\t\t\t\t\t\t\t<td>domain.jobs.</td>\r\n\t\t\t\t\t\t\t<td>IN CNAME</td>\r\n\t\t\t\t\t\t\t<td>jobs.directemployers.org.</td>\r\n\t\t\t\t\t\t</tr>\r\n\t\t\t\t\t</table>\r\n                                        <br />\r\n\t\t\t\t\t<h4>CNAME QA</h4>\r\n\t\t\t\t\t<p style=\"margin-top: 15px;\">\r\n                                                If the heading of this page is displaying your hostname instead of  <span style=\"font-weight: bold; color: #990000;\">jobs.directemployers.org</span>, then your DNS is setup correctly.\r\n\t\t\t\t\t</p>\r\n\t\t\t\t</div>\r\n\t\t\t</div>\r\n\t\t\t<div id=\"SEOfooter\">\r\n\t\t\t\t<div id=\"leftFooter\">\r\n\t\t\t\t\t\u00a92011 DirectEmployers Association, Inc., a non-profit HR consortium of leading global employers.\r\n\t\t\t\t</div>\r\n\t\t\t\t<div id=\"rightFooter\">\r\n\t\t\t\t\t<a href=\"http://www.directemployers.org/\" target=\"_blank\"><img src=\"//dn9tckvz2rpxv.cloudfront.net/jobs.directemployers.org/images/deBadgesmall.png\" border=\"0\" alt=\"\" /></a>\r\n\t\t\t\t</div>\r\n\t\t\t</div>\r\n\t\t</div>",
            browse_country_order=1,
            num_filter_items_to_show=10,
            browse_city_text="City",
            browse_state_text="State",
            browse_moc_show=False,
            home_page_template="home_page/home_page_dns_settings.html"
        ),
        Configuration(
            defaultBlurbTitle="",
            browse_facet_show=False,
            browse_country_show=False,
            header="",
            directemployers_link="http://directemployers.org/",
            meta="<link rel=\"stylesheet\" type=\"text/css\" href=\"//dn9tckvz2rpxv.cloudfront.net/css/default_config.css\" />\r\n<script type=\"text/javascript\" src=\"//dn9tckvz2rpxv.cloudfront.net/jobs.directemployers.org/cufon.js\"></script>\r\n\t\t<script type=\"text/javascript\" src=\"//dn9tckvz2rpxv.cloudfront.net/jobs.directemployers.org/Univers_LT_Std_400.font.js\"></script>\r\n\t\t<script type=\"text/javascript\">\r\n\t\t\tCufon.replace('h2,h4,table');\r\n\t\t</script>",
            fontColor="666666",
            title_tag="jobs-in",
            browse_facet_order=5,
            browse_country_text="Country",
            group=groups[-1],
            title="Default",
            wide_header="",
            browse_title_order=4,
            browse_title_text="Title",
            backgroundColor="ffffff",
            wide_footer="",
            status=2,
            num_subnav_items_to_show=9,
            browse_city_order=3,
            browse_state_order=2,
            browse_city_show=False,
            browse_state_show=False,
            browse_facet_text="Job Profiles",
            num_job_items_to_show=10,
            primaryColor="990000",
            facet_tag="new-jobs",
            browse_title_show=False,
            defaultBlurb="",
            location_tag="jobs",
            footer="<div id=\"mainContent\">\r\n\t\t\t<div id=\"SEOheader\">\r\n\t\t\t\t<img src=\"//dn9tckvz2rpxv.cloudfront.net/jobs.directemployers.org/images/DE_logo.png\" alt=\"\" />\r\n\t\t\t</div>\r\n\t\t\t<div id=\"SEOcontent\">\r\n\t\t\t\t<div id=\"contentHeader\">\r\n\t\t\t\t\t<h2>Dot Jobs Microsites and Direct SEO V3</h2>\r\n\t\t\t\t</div>\r\n\t\t\t\t<div id=\"contentContents\">\r\n\t\t\t\t\t<h4>CNAME Setup</h4>\r\n\t\t\t\t\t<p style=\"margin-top: 15px;\">\r\n\t\t\t\t\t\tAn alias, or canonical name, abbreviated CNAME, should be added to the Domain Name Server (DNS) file for your root domain<br />\r\n\t\t\t\t\t\t<span style=\"font-size: 11px;\">(Example: <span style=\"font-weight: bold; color: #990000;\">domain.jobs</span> or <span style=\"font-weight: bold; color: #990000;\">domain.com</span>).</span>\r\n\t\t\t\t\t</p>\r\n\t\t\t\t\t<p>\r\n\t\t\t\t\t\tHere is an example DNS entry for adding the subdomain <span style=\"font-weight: bold; color: #990000;\">jobs</span>.\r\n\t\t\t\t\t</p>\r\n\t\t\t\t\t<table id=\"first\">\r\n\t\t\t\t\t\t<tr>\r\n\t\t\t\t\t\t\t<td>jobs.domain.com.</td>\r\n\t\t\t\t\t\t\t<td>IN CNAME</td>\r\n\t\t\t\t\t\t\t<td>jobs.directemployers.org.</td>\r\n\t\t\t\t\t\t</tr>\r\n\t\t\t\t\t</table>\r\n\t\t\t\t\t<p style=\"font-size: 11px; margin-top: 15px;\">\r\n\t\t\t\t\t\t<span style=\"font-weight: bold;\">Note:</span><span style=\"font-style: italic;\"> The trailing periods may or may not be required, depending on your DNS server software</span>\r\n\t\t\t\t\t</p>\r\n\t\t\t\t\t<p style=\"margin-top: 15px;\">\r\n\t\t\t\t\t\tThe above line tells a web browser to get the IP address for <span style=\"font-weight: bold; color: #990000;\">jobs.domain.com</span> from the <span style=\"font-weight: bold; color: #990000;\">jobs.directemployers.org</span> DNS record. This alias allows DirectEmployers to host your SEO microsite, and is a standard method for companies to host third-party services - like blogs and RSS feeds - using their branded domain. \r\n\t\t\t\t\t</p>\r\n\t\t\t\t\t<p style=\"margin-top: 15px;\">\r\n\t\t\t\t\t\tYour company has the ultimate ownership and control over where your <span style=\"font-weight: bold; color: #990000;\">jobs.domain.com</span> hostname points, since your network administrator can change this DNS record at anytime to point to another service provider or internal server. Using a hostname based on your root domain should generate the fastest SEO ranking growth, and endear trust to the end-user who sees the hostname on a search engine results page.\r\n\t\t\t\t\t</p>\r\n\t\t\t\t\t<p style=\"margin-top: 15px;\">\r\n\t\t\t\t\t\tIf the jobs subdomain is already in use, then think about using another popular search phrase, like <span style=\"font-weight: bold; color: #990000;\">jobsearch</span>.<br />\r\n\t\t\t\t\t</p>\r\n\t\t\t\t\t<table id=\"second\">\r\n\t\t\t\t\t\t<tr>\r\n\t\t\t\t\t\t\t<td>jobsearch.domain.com.</td>\r\n\t\t\t\t\t\t\t<td>IN CNAME</td>\r\n\t\t\t\t\t\t\t<td>jobs.directemployers.org.</td>\r\n\t\t\t\t\t\t</tr>\r\n\t\t\t\t\t</table>\r\n\t\t\t\t\t<p style=\"margin-top: 15px;\">\r\n\t\t\t\t\t\tIf your company owns a .jobs top-level domain (TLD), then think about using this domain for hosting your SEO microsite. In this case, both subdomain and root domain CNAME entries are required. Here is an example DNS entry with <span style=\"font-weight: bold; color: #990000;\">www</span> as the subdomain and <span style=\"font-weight: bold; color: #990000;\">domain.jobs</span> as the root domain.\r\n\t\t\t\t\t</p>\r\n\t\t\t\t\t<table id=\"third\">\r\n\t\t\t\t\t\t<tr>\r\n\t\t\t\t\t\t\t<td>www.domain.jobs.</td>\r\n\t\t\t\t\t\t\t<td>IN CNAME</td>\r\n\t\t\t\t\t\t\t<td>jobs.directemployers.org.</td>\r\n\t\t\t\t\t\t</tr>\r\n\t\t\t\t\t\t<tr>\r\n\t\t\t\t\t\t\t<td>domain.jobs.</td>\r\n\t\t\t\t\t\t\t<td>IN CNAME</td>\r\n\t\t\t\t\t\t\t<td>jobs.directemployers.org.</td>\r\n\t\t\t\t\t\t</tr>\r\n\t\t\t\t\t</table>\r\n                                        <br />\r\n\t\t\t\t\t<h4>CNAME QA</h4>\r\n\t\t\t\t\t<p style=\"margin-top: 15px;\">\r\n                                                If the heading of this page is displaying your hostname instead of  <span style=\"font-weight: bold; color: #990000;\">jobs.directemployers.org</span>, then your DNS is setup correctly.\r\n\t\t\t\t\t</p>\r\n\t\t\t\t</div>\r\n\t\t\t</div>\r\n\t\t\t<div id=\"SEOfooter\">\r\n\t\t\t\t<div id=\"leftFooter\">\r\n\t\t\t\t\t\u00a92011 DirectEmployers Association, Inc., a non-profit HR consortium of leading global employers.\r\n\t\t\t\t</div>\r\n\t\t\t\t<div id=\"rightFooter\">\r\n\t\t\t\t\t<a href=\"http://www.directemployers.org/\" target=\"_blank\"><img src=\"//dn9tckvz2rpxv.cloudfront.net/jobs.directemployers.org/images/deBadgesmall.png\" border=\"0\" alt=\"\" /></a>\r\n\t\t\t\t</div>\r\n\t\t\t</div>\r\n\t\t</div>",
            browse_country_order=1,
            num_filter_items_to_show=10,
            browse_city_text="City",
            browse_state_text="State",
            browse_moc_show=False,
            home_page_template="home_page/home_page_dns_settings.html"
        )
    ]
    Configuration.objects.bulk_create(configurations)
    configurations = Configuration.objects.all()

    # create initial seosite
    SeoSite = apps.get_model('seo', 'seosite')
    seosite = SeoSite.objects.create(group=groups[-1])
    seosite.configurations.add(*configurations)

    # create initial social links
    ContentType = apps.get_model('contenttypes', 'contenttype')
    update_all_contenttypes()
    content_type = ContentType.objects.get(model='sociallink')
    SocialLink = apps.get_model('social_links', 'sociallink')
    social_links = [
        SocialLink(
            link_title="Member Directory",
            group=groups[-1],
            link_icon="//d2e48ltfsb5exy.cloudfront.net/content_ms/files/de-icon.png",
            link_url="http://www.directemployers.org/about/member-companies/",
            link_type="directemployers",
            content_type=content_type
        ),
        SocialLink(
            link_title="About DirectEmployers",
            group=groups[-1],
            link_icon="//d2e48ltfsb5exy.cloudfront.net/content_ms/files/de-icon.png",
            link_url="http://www.directemployers.org/about/",
            link_type="directemployers",
            content_type=content_type
        ),
        SocialLink(
            link_title="Become a Member",
            group=groups[-1],
            link_icon="//d2e48ltfsb5exy.cloudfront.net/content_ms/files/de-icon.png", 
            link_url="http://www.directemployers.org/become-a-member/", 
            link_type="directemployers",
            content_type=content_type,
        )
    ]

    SocialLink.objects.bulk_create(social_links)


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0001_initial'),
        ('seo', '0002_auto_20150717_1640'),
    ]

    operations = [
        migrations.RunPython(create_initial_data),
    ]
