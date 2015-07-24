# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('postajob', '0001_initial'),
        ('seo', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='request',
            name='owner',
            field=models.ForeignKey(to='seo.Company'),
        ),
        migrations.AddField(
            model_name='request',
            name='related_sites',
            field=models.ManyToManyField(to='seo.SeoSite'),
        ),
        migrations.AddField(
            model_name='purchasedproduct',
            name='invoice',
            field=models.ForeignKey(to='postajob.Invoice'),
        ),
        migrations.AddField(
            model_name='purchasedproduct',
            name='offline_purchase',
            field=models.ForeignKey(blank=True, to='postajob.OfflinePurchase', null=True),
        ),
        migrations.AddField(
            model_name='purchasedproduct',
            name='owner',
            field=models.ForeignKey(to='seo.Company'),
        ),
        migrations.AddField(
            model_name='purchasedproduct',
            name='product',
            field=models.ForeignKey(to='postajob.Product'),
        ),
        migrations.AddField(
            model_name='productorder',
            name='group',
            field=models.ForeignKey(to='postajob.ProductGrouping'),
        ),
        migrations.AddField(
            model_name='productorder',
            name='product',
            field=models.ForeignKey(to='postajob.Product'),
        ),
        migrations.AddField(
            model_name='productgrouping',
            name='owner',
            field=models.ForeignKey(to='seo.Company'),
        ),
        migrations.AddField(
            model_name='productgrouping',
            name='products',
            field=models.ManyToManyField(help_text=b'The products you want displayed with this grouping.', to='postajob.Product', through='postajob.ProductOrder'),
        ),
        migrations.AddField(
            model_name='product',
            name='owner',
            field=models.ForeignKey(to='seo.Company'),
        ),
        migrations.AddField(
            model_name='product',
            name='package',
            field=models.ForeignKey(to='postajob.Package'),
        ),
        migrations.AddField(
            model_name='package',
            name='content_type',
            field=models.ForeignKey(to='contenttypes.ContentType'),
        ),
        migrations.AddField(
            model_name='offlinepurchase',
            name='created_by',
            field=models.ForeignKey(related_name='created', to='seo.CompanyUser'),
        ),
        migrations.AddField(
            model_name='offlinepurchase',
            name='invoice',
            field=models.ForeignKey(to='postajob.Invoice', null=True),
        ),
        migrations.AddField(
            model_name='offlinepurchase',
            name='owner',
            field=models.ForeignKey(to='seo.Company'),
        ),
        migrations.AddField(
            model_name='offlinepurchase',
            name='products',
            field=models.ManyToManyField(to='postajob.Product', through='postajob.OfflineProduct'),
        ),
        migrations.AddField(
            model_name='offlinepurchase',
            name='redeemed_by',
            field=models.ForeignKey(related_name='redeemed', blank=True, to='seo.CompanyUser', null=True),
        ),
        migrations.AddField(
            model_name='offlineproduct',
            name='offline_purchase',
            field=models.ForeignKey(to='postajob.OfflinePurchase'),
        ),
        migrations.AddField(
            model_name='offlineproduct',
            name='product',
            field=models.ForeignKey(to='postajob.Product'),
        ),
        migrations.AddField(
            model_name='job',
            name='created_by',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='job',
            name='locations',
            field=models.ManyToManyField(related_name='jobs', to='postajob.JobLocation'),
        ),
        migrations.AddField(
            model_name='job',
            name='owner',
            field=models.ForeignKey(to='seo.Company'),
        ),
        migrations.AddField(
            model_name='invoice',
            name='invoiced_products',
            field=models.ManyToManyField(to='postajob.InvoiceProduct'),
        ),
        migrations.AddField(
            model_name='invoice',
            name='owner',
            field=models.ForeignKey(related_name='owner', to='seo.Company'),
        ),
        migrations.AddField(
            model_name='companyprofile',
            name='blocked_users',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL, blank=True),
        ),
        migrations.AddField(
            model_name='companyprofile',
            name='company',
            field=models.OneToOneField(to='seo.Company'),
        ),
        migrations.AddField(
            model_name='companyprofile',
            name='customer_of',
            field=models.ManyToManyField(related_name='customer', to='seo.Company', blank=True),
        ),
        migrations.AddField(
            model_name='sitepackage',
            name='owner',
            field=models.ForeignKey(blank=True, to='seo.Company', help_text=b'The owner of this site package. This should only be used if the site package will be used by the company for partner microsites.', null=True),
        ),
        migrations.AddField(
            model_name='sitepackage',
            name='sites',
            field=models.ManyToManyField(to='seo.SeoSite'),
        ),
        migrations.AddField(
            model_name='purchasedjob',
            name='purchased_product',
            field=models.ForeignKey(to='postajob.PurchasedProduct'),
        ),
        migrations.AlterUniqueTogether(
            name='productorder',
            unique_together=set([('product', 'group')]),
        ),
        migrations.AddField(
            model_name='job',
            name='site_packages',
            field=models.ManyToManyField(to='postajob.SitePackage', blank=True),
        ),
    ]
