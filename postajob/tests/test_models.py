from datetime import date, timedelta

from django.contrib.auth.models import Group
from django.core import mail
from django.conf import settings

from mydashboard.tests.factories import (BusinessUnitFactory, CompanyFactory,
                                         SeoSiteFactory)
from seo.tests.factories import CompanyUserFactory
from myjobs.models import User
from postajob.models import (CompanyProfile, Invoice, Job, JobLocation,
                             OfflineProduct, OfflinePurchase, Package,
                             Product, ProductGrouping, ProductOrder,
                             PurchasedJob, PurchasedProduct, Request,
                             SitePackage)
from postajob.tests.factories import (JobFactory,
                                      JobLocationFactory,
                                      OfflineProductFactory,
                                      OfflinePurchaseFactory,
                                      ProductFactory,
                                      ProductGroupingFactory,
                                      PurchasedJobFactory,
                                      PurchasedProductFactory,
                                      SitePackageFactory)
from myjobs.tests.setup import MyJobsBase


class ModelTests(MyJobsBase):
    def setUp(self):
        super(ModelTests, self).setUp()
        self.user = User.objects.create(email='user@test.email')
        self.company = CompanyFactory()
        CompanyProfile.objects.create(company=self.company)
        self.site = SeoSiteFactory()
        self.bu = BusinessUnitFactory()
        self.site.business_units.add(self.bu)
        self.site.save()
        self.company.job_source_ids.add(self.bu)
        self.company.save()

        # Use the newly created site for testing instead of secure.my.jobs.
        settings.SITE = self.site

        self.request_data = {
            'title': 'title',
            'company': self.company.id,
            'reqid': '1',
            'description': 'sadfljasdfljasdflasdfj',
            'link': 'www.google.com',
            'on_sites': '0',
            'apply_info': '',
        }

        self.request_location = {
            'city': 'Indianapolis',
            'state': 'Indiana',
            'state_short': 'IN',
            'country': 'United States',
            'country_short': 'USA',
            'zipcode': '46268',
        }

        self.site_package_data = {
            'name': 'Test Site Package',
        }

    def test_job_creation_and_deletion(self):
        locations = JobLocationFactory.create_batch(5)
        job = JobFactory(owner=self.company, created_by=self.user)
        job.locations = locations
        job.save()
        self.assertEqual(Job.objects.all().count(), 1)
        self.assertEqual(JobLocation.objects.all().count(), 5)
        job.delete()
        self.assertEqual(Job.objects.all().count(), 0)
        self.assertEqual(JobLocation.objects.all().count(), 0)

    def test_add_remove_job_locations(self):
        """
        Regression test, job locations that were removed from a job weren't
        being removed from Solr
        Tests that adding or removing locations results in Solr updates after
        a job save
        """
        job = JobFactory(owner=self.company, created_by=self.user)
        locations = JobLocationFactory.create_batch(2)
        job.locations = locations
        job.save()

        self.assertEqual(self.ms_solr.search('*:*').hits, 2)

        guid = locations[0].guid
        job.locations.remove(locations[0])
        job.save()
        self.assertEqual(self.ms_solr.search('guid:%s' % guid).hits, 0)
        self.assertEqual(self.ms_solr.search('guid:%s' %
                                             locations[1].guid).hits, 1)


    def test_job_add_to_solr(self):
        job = JobFactory(owner=self.company, created_by=self.user)
        job.locations.add(JobLocationFactory())
        job.add_to_solr()

        guids = " OR ".join(job.guids())
        query = "guid:%s" % guids
        self.assertEqual(self.ms_solr.search(query).hits, 1)

    def test_job_remove_from_solr(self):
        job = JobFactory(owner=self.company, created_by=self.user)
        locations = JobLocationFactory.create_batch(2)
        job.locations = locations
        job.save()
        job.remove_from_solr()

        guids = " OR ".join(job.guids())
        query = "guid:%s" % guids
        self.assertEqual(self.ms_solr.search(query).hits, 0)

    def test_job_generate_guid(self):
        guid = '1'*32

        # Confirm that pre-assigned guids are not being overwritten.
        location = JobLocationFactory(guid=guid)
        self.assertEqual(guid, location.guid)
        location.delete()

        # Confirm that if a guid isn't assigned one is getting assigned
        # to it properly.
        location = JobLocationFactory()
        self.assertIsNotNone(location.guid)
        self.assertNotEqual(location.guid, guid)

    def test_site_package_make_unique_for_site(self):
        package = SitePackage.objects.create(**self.site_package_data)
        package.make_unique_for_site(self.site)
        self.assertEqual(self.site.site_package, package)
        package.delete()

        package = SitePackage.objects.create(**self.site_package_data)
        for x in range(100, 110):
            site = SeoSiteFactory(id=x, domain="%s.jobs" % x)
            package.sites.add(site)

        # Site packages with existing sites associated with it should still
        # only end up with one associated site.
        site = SeoSiteFactory(id=4000, domain="4000.jobs")
        package.make_unique_for_site(site)
        self.assertEqual(site.site_package, package)

    def test_site_package_make_unique_for_company(self):
        package = SitePackage.objects.create(**self.site_package_data)
        package.make_unique_for_company(self.company)
        self.assertEqual(self.company.site_package, package)
        package.delete()

        package = SitePackage.objects.create(**self.site_package_data)
        for x in range(1000, 1003):
            site = SeoSiteFactory(id=x, domain="%s.jobs" % x)
            package.sites.add(site)
        self.assertItemsEqual(package.sites.all().values_list('id', flat=True),
                              [1000, 1001, 1002])
        for x in range(100, 103):
            site = SeoSiteFactory(id=x, domain="%s.jobs" % x)
            site.business_units.add(self.bu)
            site.save()
        # Site packages with existing sites associated with it should
        # only end up with the sites for a company.
        package.make_unique_for_company(self.company)
        self.assertEqual(self.company.site_package, package)
        self.assertItemsEqual(package.sites.all().values_list('id', flat=True),
                              [100, 101, 102, 2])

    def create_purchased_job(self, pk=None):
        if not hasattr(self, 'package'):
            self.package = SitePackageFactory(owner=self.company)
        if not hasattr(self, 'product'):
            self.product = ProductFactory(
                package=self.package, owner=self.company)
        if not hasattr(self, 'purchased_product'):
            self.purchased_product = PurchasedProductFactory(
                product=self.product, owner=self.company)
        exp_date = date.today() + timedelta(self.product.posting_window_length)
        self.assertEqual(self.purchased_product.expiration_date, exp_date)
        return PurchasedJobFactory(
            owner=self.company, created_by=self.user,
            purchased_product=self.purchased_product, pk=pk)

    def test_purchased_job_add(self):
        self.create_purchased_job()
        self.assertEqual(PurchasedJob.objects.all().count(), 1)
        self.assertEqual(SitePackage.objects.all().count(), 1)
        self.assertEqual(Request.objects.all().count(), 1)
        package = SitePackage.objects.get()
        job = PurchasedJob.objects.get()
        self.assertItemsEqual(job.site_packages.all(), [package])

    def test_purchased_job_add_to_solr(self):
        job = self.create_purchased_job()
        job.locations.add(JobLocationFactory())
        job.save()
        # Add to solr and delete from solr shouldn't be called until
        # the job is approved.
        guids = " OR ".join(job.guids())
        query = "guid:%s" % guids
        self.assertEqual(self.ms_solr.search(query).hits, 0)
        job.is_approved = True

        # Jobs won't be added/deleted until it's confirmed that the
        # purchased product is paid for as well.
        job.purchased_product.paid = True
        job.purchased_product.save()
        job.save()
        # Now that the job is approved, it should've been sent to solr.
        guids = " OR ".join(job.guids())
        query = "guid:%s" % guids
        self.assertEqual(self.ms_solr.search(query).hits, 1)

    def test_purchased_product_jobs_remaining(self):
        num_jobs_allowed = Product._meta.get_field_by_name('num_jobs_allowed')
        expected_num_jobs = num_jobs_allowed[0].default
        for x in range(50, 50 + expected_num_jobs):
            if hasattr(self, 'purchased_product'):
                self.assertTrue(self.purchased_product.can_post_more())
            self.create_purchased_job()
            expected_num_jobs -= 1
            self.assertEqual(self.purchased_product.jobs_remaining,
                             expected_num_jobs)
        self.assertFalse(self.purchased_product.can_post_more())

    def test_invoice_send_invoice_email(self):
        self.create_purchased_job()
        group, _ = Group.objects.get_or_create(name=Product.ADMIN_GROUP_NAME)

        # No one to receive the email.
        self.purchased_product.invoice.send_invoice_email()
        self.assertEqual(len(mail.outbox), 0)

        # Only recipient is specified recipient.
        self.purchased_product.invoice.send_invoice_email(other_recipients=['this@isa.test'])
        self.assertItemsEqual(mail.outbox[0].to,
                              ['this@isa.test'])

        mail.outbox = []

        # Only recipients are admins.
        user = CompanyUserFactory(user=self.user, company=self.company)
        user.group.add(group)
        user.save()
        self.purchased_product.invoice.send_invoice_email()
        self.assertItemsEqual(mail.outbox[0].to,
                              [u'user@test.email'])
        self.assertItemsEqual(mail.outbox[0].from_email,
                              'invoice@my.jobs')

        mail.outbox = []

        self.site.email_domain = 'test.domain'
        self.site.save()

        # Recipients are admins + specified recipients.
        self.purchased_product.invoice.send_invoice_email(other_recipients=['this@isa.test'])
        self.assertItemsEqual(mail.outbox[0].to,
                              ['this@isa.test', u'user@test.email'])
        self.assertEqual(mail.outbox[0].from_email,
                              'invoice@test.domain')

        mail.outbox = []

        # Only recipient is this@isa.test (no admins)
        self.purchased_product.invoice.send_invoice_email(send_to_admins=False,
                                                          other_recipients=['this@isa.test'])
        # Only one in .to should be this@isa.test
        self.assertEquals(len(mail.outbox[0].to), 1)
        self.assertItemsEqual(mail.outbox[0].to, ['this@isa.test'])

    def test_invoice_unchanged_after_purchased_product_deletion(self):
        self.create_purchased_job()
        invoice = self.purchased_product.invoice
        invoice.send_invoice_email(other_recipients=['this@isa.test'])
        old_email = mail.outbox.pop()

        self.purchased_product.delete()
        invoice.send_invoice_email(other_recipients=['this@isa.test'])
        new_email = mail.outbox.pop()

        self.assertEqual(old_email.body, new_email.body)

    def test_invoice_unchanged_after_product_changed(self):
        self.create_purchased_job()
        invoice = self.purchased_product.invoice
        invoice.send_invoice_email(other_recipients=['this@isa.test'])
        old_email = mail.outbox.pop()

        self.purchased_product.product.name = 'new name'
        self.purchased_product.product.save()
        invoice.send_invoice_email(other_recipients=['this@isa.test'])
        new_email = mail.outbox.pop()

        self.assertEqual(old_email.body, new_email.body)

    def test_productgrouping_add_delete(self):
        self.create_purchased_job()
        ProductGrouping.objects.create(display_title='Test Grouping',
                                       explanation='Test Grouping',
                                       name='Test Grouping',
                                       owner=self.company)
        self.assertEqual(ProductGrouping.objects.all().count(), 1)
        grouping = ProductGrouping.objects.get()

        order = ProductOrder.objects.create(product=self.product,
                                            group=grouping)
        grouping_products = grouping.products.all().values_list('pk', flat=True)
        self.assertItemsEqual(grouping_products, [order.product.pk])

        grouping.delete()
        self.assertEqual(ProductGrouping.objects.all().count(), 0)
        self.assertEqual(ProductOrder.objects.all().count(), 0)

    def test_request_generation(self):
        cu = CompanyUserFactory(user=self.user, company=self.company)
        cu.make_purchased_microsite_admin()

        self.create_purchased_job()
        self.assertEqual(PurchasedJob.objects.all().count(), 1)
        self.assertEqual(Request.objects.all().count(), 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertItemsEqual(mail.outbox[0].from_email,
                              'request@my.jobs')
        mail.outbox = []

        # Already approved jobs should not generate an additional request.
        PurchasedJobFactory(
            owner=self.company, created_by=self.user,
            purchased_product=self.purchased_product, is_approved=True)

        self.assertEqual(PurchasedJob.objects.all().count(), 2)
        self.assertEqual(Request.objects.all().count(), 1)
        self.assertEqual(len(mail.outbox), 0)

    def test_offlinepurchase_create_purchased_products(self):
        user = CompanyUserFactory(user=self.user, company=self.company)
        offline_purchase = OfflinePurchaseFactory(
            owner=self.company, created_by=user)
        package = SitePackageFactory(owner=self.company)
        product = ProductFactory(package=package, owner=self.company)

        for x in range(1, 15):
            PurchasedProduct.objects.all().delete()
            OfflineProduct.objects.all().delete()
            OfflineProductFactory(
                product=product,
                offline_purchase=offline_purchase,
                product_quantity=x)
            offline_purchase.create_purchased_products(self.company)
            self.assertEqual(PurchasedProduct.objects.all().count(), x)

        product_two = ProductFactory(package=package, owner=self.company)
        for x in range(1, 15):
            PurchasedProduct.objects.all().delete()
            OfflineProduct.objects.all().delete()
            OfflineProductFactory(product=product,
                                  offline_purchase=offline_purchase,
                                  product_quantity=x)
            OfflineProductFactory(product=product_two,
                                  offline_purchase=offline_purchase,
                                  product_quantity=x)
            offline_purchase.create_purchased_products(self.company)
            self.assertEqual(PurchasedProduct.objects.all().count(), x*2)

    def test_offlinepurchase_filter_by_sites(self):
        cu = CompanyUserFactory(user=self.user, company=self.company)
        for x in range(8800, 8815):
            domain = 'testsite-%s.jobs' % x
            site = SeoSiteFactory(id=x, domain=domain, name=domain)
            site_package = SitePackageFactory(owner=self.company)
            site_package.make_unique_for_site(site)
            product = ProductFactory(package=site_package, owner=self.company)
            for y in range(1, 5):
                purchase = OfflinePurchaseFactory(owner=self.company, created_by=cu)
                OfflineProduct.objects.create(product=product,
                                              offline_purchase=purchase)
            count = OfflinePurchase.objects.filter_by_sites([site]).count()
            self.assertEqual(count, 4)

        self.assertEqual(OfflinePurchase.objects.all().count(), 60)

    def test_invoice_filter_by_sites(self):
        cu = CompanyUserFactory(user=self.user, company=self.company)
        for x in range(8800, 8815):
            domain = 'testsite-%s.jobs' % x
            site = SeoSiteFactory(id=x, domain=domain, name=domain)
            site_package = SitePackageFactory(owner=self.company)
            site_package.make_unique_for_site(site)
            product = ProductFactory(package=site_package, owner=self.company)
            for y in range(1, 5):
                # OfflinePurchaseFactory() automatically creates the invoice.
                purchase = OfflinePurchaseFactory(owner=self.company, created_by=cu)
                OfflineProduct.objects.create(product=product,
                                              offline_purchase=purchase)
            # Confirm it correctly picks up Invoices associated with
            # OfflinePurchases.
            self.assertEqual(Invoice.objects.filter_by_sites([site]).count(), 4)
            for y in range(1, 5):
                # PurchasedProductFactory() also automatically creates
                # the invoice.
                PurchasedProductFactory(product=product, owner=self.company)
            # Confirm it correctly picks up Invoices associated with
            # PurchasedProducts.
            self.assertEqual(Invoice.objects.filter_by_sites([site]).count(), 8)

        self.assertEqual(Invoice.objects.all().count(), 120)

    def test_product_filter_by_sites(self):
        for x in range(8800, 8815):
            domain = 'testsite-%s.jobs' % x
            site = SeoSiteFactory(id=x, domain=domain, name=domain)
            site_package = SitePackageFactory(owner=self.company)
            site_package.make_unique_for_site(site)
            for y in range(1, 5):
                ProductFactory(package=site_package, owner=self.company)
            self.assertEqual(Product.objects.filter_by_sites([site]).count(), 4)

        self.assertEqual(Product.objects.all().count(), 60)

    def test_request_filter_by_sites(self):
        for x in range(8800, 8815):
            domain = 'testsite-%s.jobs' % x
            site = SeoSiteFactory(id=x, domain=domain, name=domain)
            site_package = SitePackageFactory(owner=self.company)
            site_package.make_unique_for_site(site)
            product = ProductFactory(package=site_package, owner=self.company)
            purchased_product = PurchasedProductFactory(product=product,
                                                        owner=self.company)
            for y in range(1, 5):
                # Unapproved purchased jobs should create Requests.
                PurchasedJobFactory(owner=self.company, created_by=self.user,
                                    purchased_product=purchased_product)
            self.assertEqual(Request.objects.filter_by_sites([site]).count(), 4)

        self.assertEqual(Request.objects.all().count(), 60)

    def test_purchasedproduct_filter_by_sites(self):
        for x in range(8800, 8815):
            domain = 'testsite-%s.jobs' % x
            site = SeoSiteFactory(id=x, domain=domain, name=domain)
            site_package = SitePackageFactory(owner=self.company)
            site_package.make_unique_for_site(site)
            for y in range(1, 5):
                product = ProductFactory(package=site_package, owner=self.company)
                PurchasedProductFactory(product=product, owner=self.company)
            count = PurchasedProduct.objects.filter_by_sites([site]).count()
            self.assertEqual(count, 4)

        self.assertEqual(PurchasedProduct.objects.all().count(), 60)

    def test_job_filter_by_sites(self):
        for x in range(8800, 8815):
            domain = 'testsite-%s.jobs' % x
            site = SeoSiteFactory(id=x, domain=domain, name=domain)
            site_package = SitePackageFactory(owner=self.company)
            site_package.make_unique_for_site(site)
            for y in range(1, 5):
                job = JobFactory(owner=self.company, created_by=self.user)
                job.site_packages.add(site_package)
                job.save()
            self.assertEqual(Job.objects.filter_by_sites([site]).count(), 4)

        self.assertEqual(Job.objects.all().count(), 60)

    def test_purchasedjob_filter_by_sites(self):
        for x in range(8800, 8815):
            domain = 'testsite-%s.jobs' % x
            site = SeoSiteFactory(id=x, domain=domain, name=domain)
            site_package = SitePackageFactory(owner=self.company)
            site_package.make_unique_for_site(site)
            product = ProductFactory(package=site_package, owner=self.company)
            purchased_product = PurchasedProductFactory(product=product,
                                                        owner=self.company)
            for y in range(1, 5):
                job = PurchasedJobFactory(owner=self.company,
                                          created_by=self.user,
                                          purchased_product=purchased_product)
                job.site_packages.add(site_package)
                job.save()
            count = PurchasedJob.objects.filter_by_sites([site]).count()
            self.assertEqual(count, 4)

        self.assertEqual(PurchasedJob.objects.all().count(), 60)

    def test_productgrouping_filter_by_sites(self):
        for x in range(8800, 8815):
            domain = 'testsite-%s.jobs' % x
            site = SeoSiteFactory(id=x, domain=domain, name=domain)
            site_package = SitePackageFactory(owner=self.company)
            site_package.make_unique_for_site(site)
            product = ProductFactory(package=site_package, owner=self.company)
            for y in range(1, 5):
                grouping = ProductGroupingFactory(owner=self.company,
                                                  display_order=y)
                ProductOrder.objects.create(product=product, group=grouping,
                                            display_order=y)
            count = ProductGrouping.objects.filter_by_sites([site]).count()
            self.assertEqual(count, 4)

        self.assertEqual(ProductGrouping.objects.all().count(), 60)

    def test_sitepackage_filter_by_sites(self):
        for x in range(8800, 8815):
            domain = 'testsite-%s.jobs' % x
            site = SeoSiteFactory(id=x, domain=domain, name=domain)
            for y in range(1, 5):
                site_package = SitePackageFactory(owner=self.company)
                site_package.sites.add(site)
                site_package.save()
            count = SitePackage.objects.filter_by_sites([site]).count()
            self.assertEqual(count, 4)
            count = Package.objects.filter_by_sites([site]).count()
            self.assertEqual(count, 4)

        self.assertEqual(SitePackage.objects.all().count(), 60)
        self.assertEqual(Package.objects.all().count(), 60)

    def test_product_filter_by_site_multiple_sites(self):
        site_in_both_packages = SeoSiteFactory(domain='secondsite.jobs', id=7)

        single_site_package = SitePackageFactory(owner=self.company)
        single_site_package.make_unique_for_site(site_in_both_packages)

        both_sites_package = SitePackageFactory(owner=self.company)
        both_sites_package.sites.add(site_in_both_packages)
        both_sites_package.sites.add(self.site)
        both_sites_package.save()

        ProductFactory(package=single_site_package, owner=self.company)
        ProductFactory(package=both_sites_package, owner=self.company)

        self.assertEqual(Product.objects.all().count(), 2)

        # Confirm that filtering by both sites gets both jobs.
        both_sites = [site_in_both_packages, self.site]
        count = Product.objects.filter_by_sites(both_sites).count()
        self.assertEqual(count, 2)

        # Confirm that filtering by the site that only has one job only
        # gets one job.
        count = Product.objects.filter_by_sites([self.site]).count()
        self.assertEqual(count, 1)

        # Confirm that filtering by the site the site that has both jobs gets
        # both jobs.
        count = Product.objects.filter_by_sites([site_in_both_packages]).count()
        self.assertEqual(count, 2)

    def test_job_filter_by_site_multiple_sites(self):
        site_in_both_packages = SeoSiteFactory(domain='secondsite.jobs', id=7)

        single_site_package = SitePackageFactory(owner=self.company)
        single_site_package.make_unique_for_site(site_in_both_packages)

        both_sites_package = SitePackageFactory(owner=self.company)
        both_sites_package.sites.add(site_in_both_packages)
        both_sites_package.sites.add(self.site)
        both_sites_package.save()

        job_on_both = JobFactory(owner=self.company, created_by=self.user)
        job_on_both.site_packages.add(both_sites_package)
        job_on_both.save()

        job_on_new_site = JobFactory(owner=self.company, created_by=self.user)
        job_on_new_site.site_packages.add(single_site_package)
        job_on_new_site.save()

        self.assertEqual(Job.objects.all().count(), 2)

        # Confirm that filtering by both sites gets both jobs.
        both_sites = [site_in_both_packages, self.site]
        count = Job.objects.filter_by_sites(both_sites).count()
        self.assertEqual(count, 2)

        # Confirm that filtering by the site that only has one job only
        # gets one job.
        self.assertEqual(Job.objects.filter_by_sites([self.site]).count(), 1)

        # Confirm that filtering by the site the site that has both jobs gets
        # both jobs.
        count = Job.objects.filter_by_sites([site_in_both_packages]).count()
        self.assertEqual(count, 2)

    def test_purchasedproduct_filter_by_site_multiple_sites(self):
        site_in_both_packages = SeoSiteFactory(domain='secondsite.jobs', id=7)

        single_site_package = SitePackageFactory(owner=self.company)
        single_site_package.make_unique_for_site(site_in_both_packages)

        both_sites_package = SitePackageFactory(owner=self.company)
        both_sites_package.sites.add(site_in_both_packages)
        both_sites_package.sites.add(self.site)
        both_sites_package.save()

        single_site_product = ProductFactory(package=single_site_package, owner=self.company)
        PurchasedProductFactory(product=single_site_product, owner=self.company)

        both_sites_product = ProductFactory(package=both_sites_package, owner=self.company)
        PurchasedProductFactory(product=both_sites_product, owner=self.company)

        self.assertEqual(PurchasedProduct.objects.all().count(), 2)

        # Confirm that filtering by both sites gets both products.
        both_sites = [site_in_both_packages, self.site]
        count = PurchasedProduct.objects.filter_by_sites(both_sites).count()
        self.assertEqual(count, 2)

        # Confirm that filtering by the site that only has one product only
        # gets one product.
        count = PurchasedProduct.objects.filter_by_sites([self.site]).count()
        self.assertEqual(count, 1)

        # Confirm that filtering by the site the site that has both products
        #  gets both jobs.
        objs = PurchasedProduct.objects.filter_by_sites([site_in_both_packages])
        count = objs.count()
        self.assertEqual(count, 2)

    def test_purchasedjob_filter_by_site_multiple_sites(self):
        site_in_both_packages = SeoSiteFactory(domain='secondsite.jobs', id=7)

        single_site_package = SitePackageFactory(owner=self.company)
        single_site_package.make_unique_for_site(site_in_both_packages)

        both_sites_package = SitePackageFactory(owner=self.company)
        both_sites_package.sites.add(site_in_both_packages)
        both_sites_package.sites.add(self.site)
        both_sites_package.save()

        single_site_product = ProductFactory(package=single_site_package, owner=self.company)
        single_site_purchasedproduct = PurchasedProductFactory(
            product=single_site_product, owner=self.company)

        both_sites_product = ProductFactory(package=both_sites_package, owner=self.company)
        both_sites_purchasedproduct = PurchasedProductFactory(
            product=both_sites_product, owner=self.company
        )

        PurchasedJobFactory(owner=self.company, created_by=self.user,
                            purchased_product=single_site_purchasedproduct)
        PurchasedJobFactory(owner=self.company, created_by=self.user,
                            purchased_product=both_sites_purchasedproduct)

        self.assertEqual(PurchasedJob.objects.all().count(), 2)

        # Confirm that filtering by both sites gets both jobs.
        both_sites = [site_in_both_packages, self.site]
        count = PurchasedJob.objects.filter_by_sites(both_sites).count()
        self.assertEqual(count, 2)

        # Confirm that filtering by the site that only has one job only
        # gets one job.
        count = PurchasedJob.objects.filter_by_sites([self.site]).count()
        self.assertEqual(count, 1)

        # Confirm that filtering by the site the site that has both jobs gets
        # both jobs.
        objs = PurchasedJob.objects.filter_by_sites([site_in_both_packages])
        count = objs.count()
        self.assertEqual(count, 2)

    def test_sitepackage_filter_by_site_multiple_sites(self):
        site_in_both_packages = SeoSiteFactory(domain='secondsite.jobs', id=7)

        single_site_package = SitePackageFactory(owner=self.company)
        single_site_package.make_unique_for_site(site_in_both_packages)

        both_sites_package = SitePackageFactory(owner=self.company)
        both_sites_package.sites.add(site_in_both_packages)
        both_sites_package.sites.add(self.site)
        both_sites_package.save()

        self.assertEqual(SitePackage.objects.all().count(), 2)
        self.assertEqual(Package.objects.all().count(), 2)

        # Confirm that filtering by both sites gets both packages.
        both_sites = [site_in_both_packages, self.site]
        count = SitePackage.objects.filter_by_sites(both_sites).count()
        self.assertEqual(count, 2)
        count = Package.objects.filter_by_sites(both_sites).count()
        self.assertEqual(count, 2)

        # Confirm that filtering by the site that only has one package only
        # gets one package.
        count = SitePackage.objects.filter_by_sites([self.site]).count()
        self.assertEqual(count, 1)
        count = Package.objects.filter_by_sites([self.site]).count()
        self.assertEqual(count, 1)

        # Confirm that filtering by the site the site that has both packages
        # gets both packages.
        objs = SitePackage.objects.filter_by_sites([site_in_both_packages])
        count = objs.count()
        self.assertEqual(count, 2)
        count = Package.objects.filter_by_sites([site_in_both_packages]).count()
        self.assertEqual(count, 2)

    def test_productgrouping_filter_by_site_multiple_sites(self):
        site_in_both_packages = SeoSiteFactory(domain='secondsite.jobs', id=7)

        single_site_package = SitePackageFactory(owner=self.company)
        single_site_package.make_unique_for_site(site_in_both_packages)

        both_sites_package = SitePackageFactory(owner=self.company)
        both_sites_package.sites.add(site_in_both_packages)
        both_sites_package.sites.add(self.site)
        both_sites_package.save()

        single_site_product = ProductFactory(package=single_site_package, owner=self.company)
        single_site_grouping = ProductGroupingFactory(owner=self.company)
        ProductOrder.objects.create(product=single_site_product,
                                    group=single_site_grouping)

        both_sites_product = ProductFactory(package=both_sites_package, owner=self.company)
        both_sites_grouping = ProductGroupingFactory(owner=self.company)
        ProductOrder.objects.create(product=both_sites_product,
                                    group=both_sites_grouping)

        # Confirm that filtering by both sites gets both groupings.
        both_sites = [site_in_both_packages, self.site]
        count = ProductGrouping.objects.filter_by_sites(both_sites).count()
        self.assertEqual(count, 2)

        # Confirm that filtering by the site that only has one grouping only
        # gets one grouping.
        count = ProductGrouping.objects.filter_by_sites([self.site]).count()
        self.assertEqual(count, 1)

        # Confirm that filtering by the site the site that has both jobs gets
        # both jobs.
        objs = ProductGrouping.objects.filter_by_sites([site_in_both_packages])
        count = objs.count()
        self.assertEqual(count, 2)

    def test_offlinepurchase_filter_by_site_multiple_sites(self):
        cu = CompanyUserFactory(user=self.user, company=self.company)
        site_in_both_packages = SeoSiteFactory(domain='secondsite.jobs', id=7)

        single_site_package = SitePackageFactory(owner=self.company)
        single_site_package.make_unique_for_site(site_in_both_packages)

        both_sites_package = SitePackageFactory(owner=self.company)
        both_sites_package.sites.add(site_in_both_packages)
        both_sites_package.sites.add(self.site)
        both_sites_package.save()

        single_site_product = ProductFactory(package=single_site_package, owner=self.company)
        single_site_purchase = OfflinePurchaseFactory(owner=self.company, created_by=cu)
        OfflineProduct.objects.create(product=single_site_product,
                                      offline_purchase=single_site_purchase)

        both_sites_product = ProductFactory(package=both_sites_package, owner=self.company)
        both_sites_purchase = OfflinePurchaseFactory(owner=self.company, created_by=cu)
        OfflineProduct.objects.create(product=both_sites_product,
                                      offline_purchase=both_sites_purchase)

        # Confirm that filtering by both sites gets both groupings.
        both_sites = [site_in_both_packages, self.site]
        count = OfflinePurchase.objects.filter_by_sites(both_sites).count()
        self.assertEqual(count, 2)

        # Confirm that filtering by the site that only has one grouping only
        # gets one grouping.
        count = OfflinePurchase.objects.filter_by_sites([self.site]).count()
        self.assertEqual(count, 1)

        # Confirm that filtering by the site the site that has both jobs gets
        # both jobs.
        objs = OfflinePurchase.objects.filter_by_sites([site_in_both_packages])
        count = objs.count()
        self.assertEqual(count, 2)

    def test_invoice_from_offlinepurchase_filter_by_site_multiple_sites(self):
        cu = CompanyUserFactory(user=self.user, company=self.company)
        site_in_both_packages = SeoSiteFactory(domain='secondsite.jobs', id=7)

        single_site_package = SitePackageFactory(owner=self.company)
        single_site_package.make_unique_for_site(site_in_both_packages)

        both_sites_package = SitePackageFactory(owner=self.company)
        both_sites_package.sites.add(site_in_both_packages)
        both_sites_package.sites.add(self.site)
        both_sites_package.save()

        single_site_product = ProductFactory(package=single_site_package, owner=self.company)
        single_site_purchase = OfflinePurchaseFactory(owner=self.company, created_by=cu)
        OfflineProduct.objects.create(product=single_site_product,
                                      offline_purchase=single_site_purchase)

        both_sites_product = ProductFactory(package=both_sites_package, owner=self.company)
        both_sites_purchase = OfflinePurchaseFactory(owner=self.company, created_by=cu)
        OfflineProduct.objects.create(product=both_sites_product,
                                      offline_purchase=both_sites_purchase)

        # Confirm that filtering by both sites gets both groupings.
        both_sites = [site_in_both_packages, self.site]
        count = Invoice.objects.filter_by_sites(both_sites).count()
        self.assertEqual(count, 2)

        # Confirm that filtering by the site that only has one grouping only
        # gets one grouping.
        count = Invoice.objects.filter_by_sites([self.site]).count()
        self.assertEqual(count, 1)

        # Confirm that filtering by the site the site that has both jobs gets
        # both jobs.
        count = Invoice.objects.filter_by_sites([site_in_both_packages]).count()
        self.assertEqual(count, 2)

    def test_invoice_from_purchasedproduct_filter_by_site_multiple_sites(self):
        site_in_both_packages = SeoSiteFactory(domain='secondsite.jobs', id=7)

        single_site_package = SitePackageFactory(owner=self.company)
        single_site_package.make_unique_for_site(site_in_both_packages)

        both_sites_package = SitePackageFactory(owner=self.company)
        both_sites_package.sites.add(site_in_both_packages)
        both_sites_package.sites.add(self.site)
        both_sites_package.save()

        single_site_product = ProductFactory(package=single_site_package, owner=self.company)
        PurchasedProductFactory(product=single_site_product, owner=self.company)

        both_sites_product = ProductFactory(package=both_sites_package, owner=self.company)
        PurchasedProductFactory(product=both_sites_product, owner=self.company)

        self.assertEqual(Invoice.objects.all().count(), 2)

        # Confirm that filtering by both sites gets both products.
        both_sites = [site_in_both_packages, self.site]
        count = Invoice.objects.filter_by_sites(both_sites).count()
        self.assertEqual(count, 2)

        # Confirm that filtering by the site that only has one product only
        # gets one product.
        count = Invoice.objects.filter_by_sites([self.site]).count()
        self.assertEqual(count, 1)

        # Confirm that filtering by the site the site that has both products
        #  gets both jobs.
        count = Invoice.objects.filter_by_sites([site_in_both_packages]).count()
        self.assertEqual(count, 2)

    def test_request_filter_by_site_multiple_sites(self):
        site_in_both_packages = SeoSiteFactory(domain='secondsite.jobs', id=7)

        single_site_package = SitePackageFactory(owner=self.company)
        single_site_package.make_unique_for_site(site_in_both_packages)

        both_sites_package = SitePackageFactory(owner=self.company)
        both_sites_package.sites.add(site_in_both_packages)
        both_sites_package.sites.add(self.site)
        both_sites_package.save()

        single_site_product = ProductFactory(package=single_site_package, owner=self.company)
        single_site_purchasedproduct = PurchasedProductFactory(
            product=single_site_product, owner=self.company)
        # Unapproved PurchasedJobs generate Requests.
        PurchasedJobFactory(owner=self.company, created_by=self.user,
                            purchased_product=single_site_purchasedproduct)

        both_sites_product = ProductFactory(package=both_sites_package, owner=self.company)
        both_sites_purchasedproduct = PurchasedProductFactory(
            product=both_sites_product, owner=self.company)
        PurchasedJobFactory(owner=self.company, created_by=self.user,
                            purchased_product=both_sites_purchasedproduct)

        self.assertEqual(Request.objects.all().count(), 2)

        # Confirm that filtering by both sites gets both products.
        both_sites = [site_in_both_packages, self.site]
        count = Request.objects.filter_by_sites(both_sites).count()
        self.assertEqual(count, 2)

        # Confirm that filtering by the site that only has one product only
        # gets one product.
        count = Request.objects.filter_by_sites([self.site]).count()
        self.assertEqual(count, 1)

        # Confirm that filtering by the site the site that has both products
        #  gets both jobs.
        count = Request.objects.filter_by_sites([site_in_both_packages]).count()
        self.assertEqual(count, 2)

    def test_request_on_purchasedjob_update(self):
        # Creating a PurchasedJob for a Product that requires approval
        # creates a Request
        job = PurchasedJobFactory(owner=self.company, created_by=self.user)
        self.assertEqual(Request.objects.count(), 1)

        # Re-saving that job should not create a new request.
        job.save()
        self.assertEqual(Request.objects.count(), 1)

        # Approving the job should also not create a new request.
        job.is_approved = True
        job.save()
        self.assertEqual(Request.objects.count(), 1)

        # Marking the job as not approved and saving it should not create
        # a new request if no action was taken on the old request.
        job.is_approved = False
        job.save()
        self.assertEqual(Request.objects.count(), 1)

        # Marking the job as not approved and saving it should create
        # a new request if there is no pending request.
        request = Request.objects.get()
        request.action_taken = True
        request.save()
        job.save()
        self.assertEqual(Request.objects.count(), 2)
