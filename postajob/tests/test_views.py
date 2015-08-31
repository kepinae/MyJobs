from bs4 import BeautifulSoup
from datetime import date, timedelta
from unittest import skip


from django.conf import settings
from django.core import mail
from django.core.urlresolvers import reverse

from myjobs.tests.setup import MyJobsBase
from mydashboard.tests.factories import (BusinessUnitFactory, CompanyFactory,
                                         CompanyUserFactory, SeoSiteFactory)
from myjobs.tests.factories import UserFactory
from postajob.tests.factories import (ProductFactory,
                                      OfflinePurchaseFactory,
                                      OfflineProductFactory,
                                      ProductGroupingFactory,
                                      JobFactory,
                                      PurchasedJobFactory,
                                      PurchasedProductFactory,
                                      SitePackageFactory)
from postajob.models import (CompanyProfile, Job, OfflinePurchase, Package,
                             Product, ProductGrouping, PurchasedJob,
                             PurchasedProduct, Request, SitePackage,
                             ProductOrder, JobLocation)
from seo.models import Company, SeoSite
from universal.helpers import build_url


class PostajobTestBase(MyJobsBase):
    def setUp(self):
        super(PostajobTestBase, self).setUp()
        self.user = UserFactory(password='5UuYquA@')
        self.company = CompanyFactory(product_access=True, posting_access=True)

        self.site = SeoSiteFactory(canonical_company=self.company)
        self.bu = BusinessUnitFactory()
        self.site.business_units.add(self.bu)
        self.site.save()
        self.company.job_source_ids.add(self.bu)
        self.company.save()
        self.company_user = CompanyUserFactory(user=self.user,
                                               company=self.company)
        SitePackageFactory(owner=self.company)
        self.package = Package.objects.get()
        self.sitepackage = SitePackage.objects.get()
        self.sitepackage.sites.add(self.site)
        self.product = ProductFactory(package=self.package, owner=self.company)

        self.login_user()

    def login_user(self, user=None):
        if not user:
            user = self.user
        self.client.post(reverse('home'),
                         data={
                             'username': user.email,
                             'password': '5UuYquA@',
                             'action': 'login',
                             })


class ViewTests(PostajobTestBase):
    def setUp(self):
        super(ViewTests, self).setUp()
        CompanyProfile.objects.create(
            company=self.company,
            address_line_one='123 Somewhere Rd',
            city='Indianapolis',
            state='Indiana',
            country='United States',
            zipcode='46268',
            authorize_net_login=settings.TESTING_CC_AUTH['api_id'],
            authorize_net_transaction_key=settings.TESTING_CC_AUTH['transaction_key'])

        self.choices_data = ('{"countries":[{"code":"United States", '
                             '"name":"United States"}], '
                             '"regions":[{"code":"Indiana", '
                             '"name":"Indiana"}] }')
        self.side_effect = [self.choices_data for x in range(0, 50)]

        self.location_management_form_data = {
            'form-TOTAL_FORMS': '1',
            'form-INITIAL_FORMS': '0',
            'form-MAX_NUM_FORMS': '5',
            'form-0-city': 'Indianapolis',
            'form-0-state': 'Indiana',
            'form-0-country': 'United States'
        }

        # Form data
        self.product_form_data = {
            'package': str(self.package.pk),
            'owner': str(self.company.pk),
            'name': 'Test Product',
            'cost': '5',
            'posting_window_length': 30,
            'max_job_length': 30,
            'job_limit': 'specific',
            'num_jobs_allowed': '5',
            'description': 'Test product description.'
        }

        self.productgrouping_form_data = {
            'products': str(self.product.pk),
            'display_order': 10,
            'display_title': 'Test Grouping',
            'explanation': 'Test grouping explanation.',
            'name': 'Test Gruping',
            'owner': str(self.company.pk)
        }

        self.job_form_data = {
            'description': 'Description',
            'title': 'Job Form Data Title',
            'owner': str(self.company.pk),
            'reqid': '123456',
            'apply_info': '',
            'zipcode': '46268',
            'apply_link': 'www.google.com',
            'apply_email': '',
            'apply_type': 'link',
            'post_to': 'network',
            'date_expired': '15'
        }

        self.purchasedjob_form_data = {
            'description': 'Description',
            'title': 'Job Form Data Title',
            'owner': str(self.company.pk),
            'reqid': '123456',
            'apply_info': '',
            'apply_link': 'www.google.com',
            'apply_email': '',
            'apply_type': 'link',
            'post_to': 'network',
            'date_expired': '15'
        }

        self.purchasedproduct_form_data = {
            'address_line_one': '123 Street Rd.',
            'card_number': '4007000000027',
            'city': 'Indianapolis',
            'country': 'United States',
            'cvv': '123',
            'exp_date_0': (date.today().month + 1) % 12 or 12,
            'exp_date_1': date.today().year + 5,
            'first_name': 'John',
            'last_name': 'Smith',
            'state': 'Indiana',
            'zipcode': '46268',
        }

        self.offlinepurchase_form_data = {
            'purchasing_company': '',
            str(self.product.pk): 1,
        }

        self.companyprofile_form_data = {
            'company_name': self.company.name,
            'address_line_one': '123 Street Rd.',
            'city': 'Indianapolis',
            'country': 'United States',
            'state': 'Indiana',
            'zipcode': '46268',
            'phone': '111-111-1111',
            'outgoing_email_domain': 'my.jobs'
        }

        for form_data in [self.job_form_data, self.purchasedjob_form_data]:
            form_data.update(self.location_management_form_data)

    def test_job_access_not_company_user(self):
        self.company_user.delete()

        response = self.client.post(reverse('jobs_overview'))
        self.assertEqual(response.status_code, 404)
        response = self.client.post(reverse('job_add'))
        self.assertEqual(response.status_code, 404)
        response = self.client.post(reverse('job_delete', kwargs={'pk': 1}))
        self.assertEqual(response.status_code, 404)
        response = self.client.post(reverse('job_update', kwargs={'pk': 1}))
        self.assertEqual(response.status_code, 404)

    def test_admin_access_no_site_package(self):
        """
        Ensure that pages that would be useless without a site package have
        their content replaced by a friendly reminder to have a site package
        created.
        """
        self.sitepackage.sites.clear()
        
        for url in ['request', 'offlinepurchase_add', 'product_add',
                    'productgrouping_add']:
            response = self.client.get(reverse(url), HTTP_HOST='test.jobs')
            self.assertEqual(response.status_code, 200)
            self.assertIn("Please contact your member representative to "
                          "activate this feature.",
                          response.content)

    def test_job_access_not_for_company(self):
        new_company = CompanyFactory(name='Another Company', pk=1000)
        job = JobFactory(owner=new_company, created_by=self.user)
        kwargs = {'pk': job.pk}

        response = self.client.post(reverse('job_delete', kwargs=kwargs))
        self.assertEqual(response.status_code, 404)
        response = self.client.post(reverse('job_update', kwargs=kwargs))
        self.assertEqual(response.status_code, 404)

        # Make sure that the call to job_delete didn't delete the job
        self.assertEqual(Job.objects.all().count(), 1)

    def test_job_access_allowed(self):
        resp_url = reverse('jobs_overview')

        job = JobFactory(owner=self.company, created_by=self.user)
        kwargs = {'pk': job.pk}

        response = self.client.post(reverse('job_update', kwargs=kwargs),
                                    data=self.job_form_data)
        self.assertRedirects(response, resp_url, status_code=302)

    def test_job_add(self):
        response = self.client.post(reverse('job_add'), data=self.job_form_data,
                                    follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Job.objects.all().count(), 1)

    def test_job_update(self):
        job = JobFactory(owner=self.company, created_by=self.user)
        kwargs = {'pk': job.pk}

        self.assertNotEqual(job.title, self.job_form_data['title'])
        response = self.client.post(reverse('job_update', kwargs=kwargs),
                                    data=self.job_form_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Job.objects.all().count(), 1)
        # Ensure we're working with the most recent copy of the job.
        job = Job.objects.get()
        self.assertEqual(job.title, self.job_form_data['title'])

    def test_job_delete(self):
        job = JobFactory(owner=self.company, created_by=self.user)
        kwargs = {'pk': job.pk}

        response = self.client.post(reverse('job_delete', kwargs=kwargs))
        self.assertEqual(response.status_code, 404)
        self.assertEqual(Job.objects.all().count(), 1)

    def test_purchasedjob_add(self):
        product = PurchasedProductFactory(
            product=self.product, owner=self.company)
        kwargs = {'product': product.pk}

        response = self.client.post(reverse('purchasedjob_add', kwargs=kwargs),
                                    data=self.purchasedjob_form_data,
                                    follow=True,
                                    HTTP_HOST='test.jobs')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(PurchasedJob.objects.count(), 1)
        self.assertEqual(Request.objects.count(), 1)

        job = PurchasedJob.objects.get()
        self.assertEqual(job.created_by, self.user)
    
    def test_purchasedjob_update(self):
        product = PurchasedProductFactory(
            product=self.product, owner=self.company)
        job = PurchasedJobFactory(
            owner=self.company, created_by=self.user, 
            purchased_product=product)
        kwargs = {'pk': job.pk}

        self.assertNotEqual(job.title, self.job_form_data['title'])
        response = self.client.post(reverse('purchasedjob_update',
                                            kwargs=kwargs),
                                    data=self.purchasedjob_form_data,
                                    follow=True,
                                    HTTP_HOST='test.jobs')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(PurchasedJob.objects.all().count(), 1)
        # Ensure we're working with the most recent copy of the job.
        job = Job.objects.get()
        self.assertEqual(job.title, self.job_form_data['title'])

    def test_purchasedjob_delete(self):
        product = PurchasedProductFactory(
            product=self.product, owner=self.company)
        job = PurchasedJobFactory(
            owner=self.company,
            created_by=self.user,
            purchased_product=product)
        kwargs = {'pk': job.pk}

        response = self.client.post(reverse('purchasedjob_delete',
                                            kwargs=kwargs),
                                            HTTP_HOST='test.jobs')
        self.assertEqual(response.status_code, 404)
        self.assertEqual(PurchasedJob.objects.all().count(), 1)

    def test_unexpire_expired_purchased_job(self):
        product = PurchasedProductFactory(
            product=self.product, owner=self.company)
        job = PurchasedJobFactory(
            owner=self.company, created_by=self.user,
            purchased_product=product)
        kwargs = {'pk': job.pk}

        self.assertFalse(job.is_expired)

        job.is_expired = True
        job.date_expired = date.today()
        job.max_expired_date = date.today() - timedelta(1)
        job.save()

        data = dict(self.purchasedjob_form_data)
        data['is_expired'] = False

        response = self.client.post(reverse('purchasedjob_update',
                                            kwargs=kwargs),
                                    data=self.purchasedjob_form_data,
                                    follow=True)
        self.assertEqual(response.status_code, 200)

        # Confirm that the job remains expired despite the attempt to
        # change it.
        job = Job.objects.get()
        self.assertTrue(job.is_expired)

    def test_purchasedjob_add_too_many(self):
        product = PurchasedProductFactory(
            product=self.product, owner=self.company)
        product.jobs_remaining = 1
        product.save()
        kwargs = {'product': product.pk}

        response = self.client.post(reverse('purchasedjob_add', kwargs=kwargs),
                                    data=self.purchasedjob_form_data,
                                    follow=True,
                                    HTTP_HOST='test.jobs')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(PurchasedJob.objects.all().count(), 1)

        response = self.client.post(reverse('purchasedjob_add', kwargs=kwargs),
                                    data=self.purchasedjob_form_data,
                                    HTTP_HOST='test.jobs')
        self.assertEqual(response.status_code, 404)

    def test_job_add_network(self):
        response = self.client.post(reverse('job_add'), data=self.job_form_data,
                                    follow=True)
        self.assertEqual(response.status_code, 200)
        job = Job.objects.get()
        self.assertItemsEqual(job.site_packages.all(),
                              [job.owner.site_package])

    def test_job_add_site(self):
        package = SitePackage.objects.create(name='')
        package.make_unique_for_site(self.site)
        self.job_form_data['post_to'] = 'site'
        self.job_form_data['site_packages'] = self.site.pk

        response = self.client.post(reverse('job_add'), data=self.job_form_data,
                                    follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Job.objects.all().count(), 1)
        job = Job.objects.get()
        # The company site_package should've never been created
        self.assertIsNone(job.owner.site_package)
        # The site_package we created for the site should be
        # the package that shows up on the job.
        self.assertIn(package.pk,
                      job.site_packages.all().values_list('pk', flat=True))

    def test_job_invalid_apply(self):
        # All three
        test_data = dict(self.job_form_data)
        test_data['apply_email'] = 'email@email.email'
        test_data['apply_info'] = 'How to apply.'
        response = self.client.post(reverse('job_add'), data=test_data)
        # The lack of the redirect (302) means that the form wasn't
        # successfully submitted.
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Job.objects.all().count(), 0)

        # Link + Email
        test_data = dict(self.job_form_data)
        test_data['apply_email'] = 'email@email.email'
        response = self.client.post(reverse('job_add'), data=test_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Job.objects.all().count(), 0)

        # Link + Info
        test_data = dict(self.job_form_data)
        test_data['apply_info'] = 'How to apply.'
        response = self.client.post(reverse('job_add'), data=test_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Job.objects.all().count(), 0)

        # Email + Info
        test_data = dict(self.job_form_data)
        test_data['apply_link'] = ''
        test_data['apply_email'] = 'email@email.email'
        test_data['apply_info'] = 'How to apply.'
        response = self.client.post(reverse('job_add'), data=test_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Job.objects.all().count(), 0)

        #Link. Should be successful.
        test_data = dict(self.job_form_data)
        response = self.client.post(reverse('job_add'), data=test_data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Job.objects.all().count(), 1)
        Job.objects.all().delete()

        # Email. Should be successful.
        test_data = dict(self.job_form_data)
        test_data['apply_link'] = ''
        test_data['apply_email'] = 'email@email.email'
        response = self.client.post(reverse('job_add'), data=test_data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Job.objects.all().count(), 1)
        Job.objects.all().delete()

        # Info. Should be successful.
        test_data = dict(self.job_form_data)
        test_data['apply_link'] = ''
        test_data['apply_info'] = 'How to apply.'
        response = self.client.post(reverse('job_add'), data=test_data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Job.objects.all().count(), 1)
        Job.objects.all().delete()

    def test_product_add(self):
        response = self.client.post(reverse('product_add'),
                                    data=self.product_form_data,
                                    follow=True,
                                    HTTP_HOST='test.jobs')
        self.assertEqual(response.status_code, 200)
        # Should get the product just added + self.product
        self.assertEqual(Product.objects.all().count(), 2)

    def test_product_add_no_authorize_acct(self):
        self.company.companyprofile.authorize_net_transaction_key = ''
        self.company.companyprofile.authorize_net_login = ''
        self.company.companyprofile.save()


        response = self.client.post(reverse('product_add'),
                                    data=self.product_form_data,
                                    follow=True,
                                    HTTP_HOST='test.jobs')
        self.assertIn('You cannot charge for jobs', response.content)

        data = dict(self.product_form_data)
        data['cost'] = 0
        data['requires_approval'] = False
        response = self.client.post(reverse('product_add'), data=data,
                                    follow=True,
                                    HTTP_HOST='test.jobs')
        self.assertIn('Free jobs require approval', response.content)

        data['requires_approval'] = True
        self.client.post(reverse('product_add'), data=data, follow=True,
                         HTTP_HOST='test.jobs')
        self.assertEqual(Product.objects.all().count(), 2)

    def test_product_update(self):
        self.product_form_data['name'] = 'New Title'
        kwargs = {'pk': self.product.pk}

        self.assertNotEqual(self.product.name, self.product_form_data['name'])
        response = self.client.post(reverse('product_update', kwargs=kwargs),
                                    data=self.product_form_data, follow=True,
                                    HTTP_HOST='test.jobs')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Product.objects.all().count(), 1)

        product = Product.objects.get()
        self.assertEqual(product.name, self.product_form_data['name'])

    def test_product_delete(self):
        self.product_form_data['name'] = 'New Title'
        kwargs = {'pk': self.product.pk}

        response = self.client.post(reverse('product_delete', kwargs=kwargs),
                                    HTTP_HOST='test.jobs')
        self.assertEqual(response.status_code, 404)

    def test_product_update_job_limit(self):
        self.product_form_data['name'] = 'New Title'
        kwargs = {'pk': self.product.pk}

        self.product_form_data['job_limit'] = 'unlimited'

        self.assertNotEqual(self.product.name, self.product_form_data['name'])
        response = self.client.post(reverse('product_update', kwargs=kwargs),
                                    data=self.product_form_data, follow=True,
                                    HTTP_HOST='test.jobs')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Product.objects.all().count(), 1)

        product = Product.objects.get()
        self.assertEqual(product.name, self.product_form_data['name'])
        self.assertEqual(product.num_jobs_allowed, 0)

    def test_productgrouping_add(self):
        response = self.client.post(reverse('productgrouping_add'),
                                    data=self.productgrouping_form_data,
                                    follow=True,
                                    HTTP_HOST='test.jobs')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ProductGrouping.objects.all().count(), 1)

    def test_productgrouping_update(self):
        group = ProductGroupingFactory(owner=self.company)
        self.productgrouping_form_data['name'] = 'New Title'
        kwargs = {'pk': group.pk}

        self.assertNotEqual(group.name, self.productgrouping_form_data['name'])
        response = self.client.post(reverse('productgrouping_update',
                                            kwargs=kwargs),
                                    data=self.productgrouping_form_data,
                                    follow=True,
                                    HTTP_HOST='test.jobs')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ProductGrouping.objects.all().count(), 1)

        group = ProductGrouping.objects.get()
        self.assertEqual(group.name, self.productgrouping_form_data['name'])

    def test_productgrouping_delete(self):
        group = ProductGroupingFactory(owner=self.company)
        self.product_form_data['name'] = 'New Title'
        kwargs = {'pk': group.pk}

        response = self.client.post(reverse('productgrouping_delete',
                                            kwargs=kwargs),
                                            HTTP_HOST='test.jobs')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(ProductGrouping.objects.all().count(), 0)

    def test_purchasedproduct_add(self):
        product = {'product': self.product.pk}

        response = self.client.post(reverse('purchasedproduct_add',
                                            kwargs=product),
                                    data=self.purchasedproduct_form_data,
                                    follow=True,
                                    HTTP_HOST='test.jobs')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(PurchasedProduct.objects.count(), 1)
        purchase = PurchasedProduct.objects.get()
        self.assertTrue(purchase.paid)
        self.assertEqual(purchase.invoice.card_last_four,
                         self.purchasedproduct_form_data['card_number'][-4:])
        self.assertEqual(purchase.invoice.card_exp_date.month,
                         self.purchasedproduct_form_data['exp_date_0'])
        self.assertEqual(purchase.invoice.card_exp_date.year,
                         self.purchasedproduct_form_data['exp_date_1'])
        exp_date = date.today() + timedelta(self.product.posting_window_length)
        self.assertEqual(purchase.expiration_date, exp_date)
        self.assertEqual(len(mail.outbox), 1)

    def test_purchasedproduct_add_free_product_existing_company_with_address(self):
        self.assertEqual(PurchasedProduct.objects.all().count(), 0)
        self.product.cost = 0
        self.product.save()
        product = {'product': self.product.pk}
        response = self.client.get(reverse('purchasedproduct_add',
                                           kwargs=product),
                                   follow=True,
                                   HTTP_HOST='test.jobs')
        url = reverse('purchasedproducts_overview')
        self.assertTrue(response.redirect_chain[-1][0].endswith(url))
        self.assertEqual(PurchasedProduct.objects.all().count(), 1)

    def test_purchasedproduct_add_free_product_existing_company_no_address(self):
        self.assertEqual(PurchasedProduct.objects.all().count(), 0)
        self.product.cost = 0
        self.product.save()
        self.company.companyprofile.delete()
        product = {'product': self.product.pk}
        data = dict(self.purchasedproduct_form_data)
        del data['card_number']
        del data['cvv']
        del data['exp_date_0']
        del data['exp_date_1']
        self.client.post(reverse('purchasedproduct_add', kwargs=product),
                         data=data,
                         follow=True,
                         HTTP_HOST='test.jobs')
        self.assertEqual(PurchasedProduct.objects.all().count(), 1)

    def test_purchasedproduct_add_free_product_no_company(self):
        new_user = UserFactory(email='test@test.test')
        self.login_user(user=new_user)
        self.assertEqual(PurchasedProduct.objects.all().count(), 0)
        self.product.cost = 0
        self.product.save()
        self.company.companyprofile.delete()
        product = {'product': self.product.pk}
        data = dict(self.purchasedproduct_form_data)
        del data['card_number']
        del data['cvv']
        del data['exp_date_0']
        del data['exp_date_1']
        data['company_name'] = 'Test New Company'
        self.client.post(reverse('purchasedproduct_add', kwargs=product),
                         data=data,
                         follow=True,
                         HTTP_HOST='test.jobs')
        Company.objects.get(name=data['company_name'])
        self.assertEqual(PurchasedProduct.objects.all().count(), 1)

    def test_purchasedproduct_add_card_declined(self):
        # Change the card number so it doesn't artificially get declined
        # due to duplicate transactions.
        self.purchasedproduct_form_data['card_number'] = 4012888818888
        # 70.02 should always result in a decline for test cards.
        self.product.cost = 70.02
        self.product.save()
        product = {'product': self.product.pk}
        response = self.client.post(reverse('purchasedproduct_add',
                                            kwargs=product),
                                    data=self.purchasedproduct_form_data,
                                    follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(PurchasedProduct.objects.all().count(), 0)

    def test_purchasedproduct_update(self):
        purchased_product = PurchasedProductFactory(
            product=self.product, owner=self.company)
        kwargs = {'pk': purchased_product.pk}

        response = self.client.post(reverse('purchasedproduct_update',
                                            kwargs=kwargs),
                                            HTTP_HOST='test.jobs')
        self.assertEqual(response.status_code, 404)

    def test_purchasedproduct_delete(self):
        purchased_product = PurchasedProductFactory(
            product=self.product, owner=self.company)
    
        kwargs = {'pk': purchased_product.pk}

        response = self.client.post(reverse('purchasedproduct_delete',
                                            kwargs=kwargs))
        self.assertEqual(response.status_code, 404)

    def test_purchasedjob_access_not_company_user(self):
        response = self.client.post(reverse('purchasedproducts_overview'),
                                    HTTP_HOST='test.jobs')
        self.assertEqual(response.status_code, 200)
        self.company_user.delete()

        response = self.client.post(reverse('purchasedproducts_overview'),
                                            HTTP_HOST='test.jobs')
        self.assertEqual(response.status_code, 404)

    def test_purchasedproducts_active_expired(self):
        PurchasedProductFactory.create_batch(3, product=self.product,
                                             owner=self.company)

        expired_product = PurchasedProductFactory(product=self.product,
                                                  owner=self.company)
        expired_product.expiration_date = date.today()-timedelta(days=1)
        expired_product.save()
        response = self.client.post(reverse('purchasedproduct'),
                                    HTTP_HOST='test.jobs')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["active_products"]), 3)
        self.assertEqual(len(response.context["expired_products"]), 1)

    def test_purchasedjobs_active_expired(self):
        purchased_product = PurchasedProductFactory(product=self.product,
                                                    owner=self.company)
        PurchasedJobFactory.create_batch(
            3, purchased_product=purchased_product, owner=self.company,
            created_by=self.user)
        expired_job = PurchasedJobFactory(purchased_product=purchased_product,
                                          owner=self.company,
                                          created_by=self.user)
        expired_job.is_expired = True
        expired_job.save()

        response = self.client.post(
            reverse('purchasedjobs',
                    kwargs={'purchased_product': purchased_product.id}),
            HTTP_HOST='test.jobs')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['active_jobs']), 3)
        self.assertEqual(len(response.context['expired_jobs']), 1)

    def test_is_company_user(self):
        # Current user is a CompanyUser
        params = {'email': self.user.email}
        url = build_url(reverse('is_company_user'), params)
        response = self.client.post(url)
        self.assertEqual(response.content, 'true')

        # Non-existant user is not a CompanyUser
        params = {'email': 'thisemail@is.madeup'}
        url = build_url(reverse('is_company_user'), params)
        response = self.client.post(url)
        self.assertEqual(response.content, 'false')

        # Generic User is not a CompanyUser.
        user = UserFactory(email='anew@user.email')
        params = {'email': user.email}
        url = build_url(reverse('is_company_user'), params)
        response = self.client.post(url)
        self.assertEqual(response.content, 'false')

        # Is inaccessable to non-CompanyUsers.
        self.company_user.delete()
        params = {'email': self.user.email}
        url = build_url(reverse('is_company_user'), params)
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)

    def test_offlinepurchase_redeem_not_logged_in(self):
        self.client.logout()
        response = self.client.get(reverse('offlinepurchase_redeem'),
                                   follow=True,
                                   HTTP_HOST='test.jobs')
        self.assertEqual(response.request['PATH_INFO'], reverse('login'))
        self.assertEqual(response.status_code, 200)

    def test_offlinepurchase_redeem_new_company(self):
        offline_purchase = OfflinePurchaseFactory(
            owner=self.company, created_by=self.company_user)
        OfflineProductFactory(
            product=self.product, offline_purchase=offline_purchase,
            product_quantity=3)
        self.client.logout()
        self.login_user(UserFactory(email='newemail@test.test'))

        data = {
            'company_name': 'A new company',
            'address_line_one': '123 Place Road',
            'address_line_two': 'Suite 1',
            'city': 'Indianapolis',
            'state': 'Indiana',
            'country': 'United States',
            'zipcode': '46268',
            'redemption_id': offline_purchase.redemption_uid
        }
        current_product_count = PurchasedProduct.objects.all().count()
        response = self.client.post(reverse('offlinepurchase_redeem'),
                                    data=data, follow=True,
                                    HTTP_HOST='test.jobs')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(current_product_count + 3,
                         PurchasedProduct.objects.all().count())

        # Make sure we're working with the most recent copy of the object.
        offline_purchase = OfflinePurchase.objects.get()
        self.assertIsNotNone(offline_purchase.redeemed_on)
        self.assertIsNotNone(offline_purchase.redeemed_by)

        new_company = offline_purchase.redeemed_by.company
        self.assertEqual(new_company.name, data['company_name'])
        self.assertTrue(new_company, 'companyprofile')

    def test_offlinepurchase_redeem_duplicate_company_name(self):
        offline_purchase = OfflinePurchaseFactory(
            owner=self.company, created_by=self.company_user)
        OfflineProductFactory(
            product=self.product, offline_purchase=offline_purchase,
            product_quantity=3)
        self.client.logout()
        self.login_user(UserFactory(email='newemail@test.test'))

        data = {
            'company_name': self.company.name,
            'address_line_one': '123 Place Road',
            'address_line_two': 'Suite 1',
            'city': 'Indianapolis',
            'state': 'Indiana',
            'country': 'United States',
            'zipcode': '46268',
            'redemption_id': offline_purchase.redemption_uid
        }
        current_product_count = PurchasedProduct.objects.all().count()
        response = self.client.post(reverse('offlinepurchase_redeem'),
                                    data=data, follow=True,
                                    HTTP_HOST='test.jobs')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(current_product_count,
                         PurchasedProduct.objects.all().count())
        self.assertEqual(response.request['PATH_INFO'],
                         reverse('offlinepurchase_redeem'))

    def test_offlinepurchase_redeem(self):
        offline_purchase = OfflinePurchaseFactory(
            owner=self.company, created_by=self.company_user)
        OfflineProductFactory(
            product=self.product, offline_purchase=offline_purchase,
            product_quantity=3)

        data = {'redemption_id': offline_purchase.redemption_uid}
        current_product_count = PurchasedProduct.objects.all().count()
        response = self.client.post(reverse('offlinepurchase_redeem'),
                                    data=data, follow=True,
                                    HTTP_HOST='test.jobs')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(current_product_count + 3,
                         PurchasedProduct.objects.all().count())

        # Make sure we're working with the most recent copy of the object.
        offline_purchase = OfflinePurchase.objects.get()
        self.assertIsNotNone(offline_purchase.redeemed_on)
        self.assertIsNotNone(offline_purchase.redeemed_by)

    def test_offlinepurchase_redeem_invalid(self):
        data = {'redemption_id': 1}
        current_product_count = PurchasedProduct.objects.all().count()
        response = self.client.post(reverse('offlinepurchase_redeem'),
                                    data=data, follow=True,
                                    HTTP_HOST='test.jobs')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(current_product_count,
                         PurchasedProduct.objects.all().count())

    def test_offlinepurchase_redeem_already_redeemed(self):
        offline_purchase = OfflinePurchaseFactory(
            owner=self.company, created_by=self.company_user,
            redeemed_on=date.today(), redeemed_by=self.company_user)
        OfflineProductFactory(
            product=self.product,
            offline_purchase=offline_purchase,
            product_quantity=7)

        data = {'redemption_id': offline_purchase.redemption_uid}
        current_product_count = PurchasedProduct.objects.all().count()
        response = self.client.post(reverse('offlinepurchase_redeem'),
                                    data=data, follow=True,
                                    HTTP_HOST='test.jobs')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(current_product_count,
                         PurchasedProduct.objects.all().count())

    def test_offlinepurchase_add_without_company(self):
        response = self.client.post(reverse('offlinepurchase_add'),
                                    data=self.offlinepurchase_form_data,
                                    follow=True,
                                    HTTP_HOST='test.jobs')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(OfflinePurchase.objects.all().count(), 1)
        offline_purchase = OfflinePurchase.objects.get()
        self.assertIn(offline_purchase.redemption_uid, response.content)

    @skip('Feature disabled for now.')
    def test_offlinepurchase_add_with_company(self):
        self.offlinepurchase_form_data['purchasing_company'] = str(self.company.pk)
        response = self.client.post(reverse('offlinepurchase_add'),
                                    data=self.offlinepurchase_form_data,
                                    follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(OfflinePurchase.objects.all().count(), 1)
        offline_purchase = OfflinePurchase.objects.get()
        self.assertNotIn(offline_purchase.redemption_uid, response.content)
        self.assertIsNotNone(offline_purchase.redeemed_on)

    def test_offlinepurchase_update(self):
        offline_purchase = OfflinePurchaseFactory(
            owner=self.company, created_by=self.company_user)
        kwargs = {'pk': offline_purchase.pk}

        response = self.client.post(reverse('offlinepurchase_update',
                                            kwargs=kwargs),
                                    HTTP_HOST='test.jobs')
        self.assertEqual(response.status_code, 404)

    def test_offlinepurchase_delete(self):
        offline_purchase = OfflinePurchaseFactory(
            owner=self.company, created_by=self.company_user)
        kwargs = {'pk': offline_purchase.pk}

        response = self.client.post(reverse('offlinepurchase_delete',
                                            kwargs=kwargs),
                                    follow=True,
                                    HTTP_HOST='test.jobs')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(OfflinePurchase.objects.all().count(), 0)

    def test_offlinepurchase_delete_already_redeemed(self):
        offline_purchase = OfflinePurchaseFactory(
            owner=self.company, created_by=self.company_user,
            redeemed_on=date.today(), redeemed_by=self.company_user)
        kwargs = {'pk': offline_purchase.pk}

        response = self.client.post(reverse('offlinepurchase_delete',
                                            kwargs=kwargs), follow=True,
                                            HTTP_HOST='test.jobs')
        self.assertEqual(response.status_code, 404)
        self.assertEqual(OfflinePurchase.objects.all().count(), 1)

    def test_update_companyprofile(self):
        self.client.post(reverse('companyprofile_add'),
                         data=self.companyprofile_form_data, follow=True,
                         HTTP_HOST='test.jobs')
        profile = CompanyProfile.objects.get()
        self.assertEqual(profile.address_line_one,
                         self.companyprofile_form_data['address_line_one'])

        self.company.user_created = True
        self.company.save()
        self.companyprofile_form_data['company_name'] = 'A New Name'
        self.client.post(reverse('companyprofile_add'),
                         data=self.companyprofile_form_data, follow=True,
                         HTTP_HOST='test.jobs')
        profile = CompanyProfile.objects.get()
        self.assertEqual(profile.company.name,
                         self.companyprofile_form_data['company_name'])

    def test_list_products_jsonp(self):
        # view should work without being logged in
        self.client.logout()
        response = self.client.get(reverse('product_listing'),
                                   HTTP_HOST='test.jobs')
        # When an item in the chain of objects from SeoSite->ProductGrouping
        # is missing, we return text stating that there is nothing to purchase
        self.assertTrue('There are no products configured for purchase'
                        in response.content)
        site_package = SitePackageFactory()
        site_package.sites.add(SeoSite.objects.get(id=1), settings.SITE)
        self.product.package = site_package
        self.product.save()
        productgrouping = ProductGroupingFactory(owner=self.company)
        ProductOrder(product=self.product, group=productgrouping).save()

        response = self.client.get(reverse('product_listing'),
                                   HTTP_HOST='test.jobs')
        for text in [productgrouping.display_title, productgrouping.explanation,
                     unicode(self.product)]:
            # When the entire chain of objects exists, the return HTML should
            # include elements from the relevant ProductGrouping and Product
            # instances
            self.assertTrue(text in response.content)
    
    def test_job_add_and_remove_locations(self):
        location = {
            'form-0-city': 'Indianapolis',
            'form-0-state': 'Indiana',
            'form-0-country': 'United States',
            'form-0-zipcode': '12345',
        }
        self.job_form_data['form-TOTAL_FORMS'] = 1
        self.job_form_data.update(location)
        self.assertEqual(Job.objects.count(), 0)
        self.assertEqual(JobLocation.objects.count(), 0)
        self.client.post(reverse('job_add'), data=self.job_form_data,
                         follow=True)
        self.assertEqual(Job.objects.count(), 1)
        self.assertEqual(JobLocation.objects.count(), 1)

        job = Job.objects.get()
        location = job.locations.first()
        self.job_form_data['id'] = job.pk
        self.job_form_data['form-TOTAL_FORMS'] = 2
        self.job_form_data.update({
            'form-0-id': location.pk,
            'form-0-DELETE': 'on',
            'form-1-city': 'Muncie',
            'form-1-state': 'Indiana',
            'form-1-country': 'United States',
        })
        self.client.post(reverse('job_update', args=[job.pk]),
                         data=self.job_form_data, follow=True)
        self.assertEqual(JobLocation.objects.count(), 1)

    def test_purchasedjob_form(self):
        purchased_product = PurchasedProductFactory(
            product=self.product, owner=self.company)

        site = SeoSiteFactory(domain='indiana.jobs', id=3)
        site.business_units.add(self.bu)
        self.sitepackage.sites.add(site)
        product = {'product': purchased_product.pk}
        response = self.client.get(reverse('purchasedjob_add',
                                           kwargs=product))
        soup = BeautifulSoup(response.content)
        site_packages = soup.select('[id^=id_site_packages]')[0]
        site_packages = site_packages.text.strip().split('\n')
        self.assertEqual(len(site_packages), 2)
        self.assertItemsEqual([self.site.domain, site.domain],
                              site_packages)

    def test_purchasedjob_locations(self):
        purchased_product = PurchasedProductFactory(
            product=self.product, owner=self.company)

        site = SeoSiteFactory(domain='indiana.jobs', id=3)
        site.business_units.add(self.bu)
        self.sitepackage.sites.add(site)
        site.sitepackage_set.add(self.sitepackage)
        location = {
            'form-0-city': 'Indianapolis',
            'form-0-state': 'Indiana',
            'form-0-country': 'United States',
            'form-0-zipcode': '12345',
        }
        self.job_form_data['form-TOTAL_FORMS'] = 1
        self.job_form_data.update(location)
        self.assertEqual(Job.objects.count(), 0)
        self.assertEqual(JobLocation.objects.count(), 0)
        self.client.post(reverse('purchasedjob_add',
                                 args=[purchased_product.pk]),
                         data=self.job_form_data, follow=True,
                         HTTP_HOST='test.jobs')
        self.assertEqual(PurchasedJob.objects.count(), 1)
        self.assertEqual(JobLocation.objects.count(), 1)
        job = PurchasedJob.objects.get()
        location = job.locations.first()
        self.job_form_data['id'] = job.pk
        self.job_form_data['form-TOTAL_FORMS'] = 2
        self.job_form_data.update({
            'form-0-id': location.pk,
            'form-0-DELETE': 'on',
            'form-1-city': 'Muncie',
            'form-1-state': 'Indiana',
            'form-1-country': 'United States'
        })
        self.client.post(reverse('purchasedjob_update', args=[job.pk]),
                         data=self.job_form_data, follow=True,
                         HTTP_HOST='test.jobs')
        self.assertEqual(JobLocation.objects.count(), 1)

    def test_view_request_posted_by_unrelated_company(self):
        company = CompanyFactory(id=2, name='new company')
        user = UserFactory(email='new_company_user@email.com')
        CompanyUserFactory(user=user, company=company)
        product = PurchasedProductFactory(
            product=self.product, owner=company)
        PurchasedJobFactory(owner=company, created_by=user,
                            purchased_product=product)
        request = Request.objects.get()
        response = self.client.get(
            reverse('view_request',
                    args=[request.pk]),
            HTTP_HOST='test.jobs')
        self.assertFalse(self.user in company.admins.all())
        self.assertEqual(response.status_code, 200)

    def test_accessing_wrong_company_admin(self):
        """
        Trying to access the admin pages for a site that is a part of a package
        which isn't own by a company to which you belong should raise a 404.
        """
        self.company_user.company = CompanyFactory(pk=41, name="Wrong Company")
        self.company_user.save()

        for page in ['view_job', 'view_invoice', 
                     'purchasedmicrosite_admin_overview', 'admin_products',
                     'admin_groupings', 'admin_offlinepurchase',
                     'admin_purchasedproduct', 'view_request', 
                     'process_admin_request', 'resend_invoice', 
                     'block_user_management']:

            response = self.client.get(
                reverse('purchasedmicrosite_admin_overview'),
                HTTP_HOST='test.jobs')

        self.assertEqual(response.status_code, 404)


class PurchasedJobActionTests(PostajobTestBase):
    def setUp(self):
        super(PurchasedJobActionTests, self).setUp()
        self.purchased_product = PurchasedProductFactory(
            product=self.product, owner=self.company)
        self.job = PurchasedJobFactory(
            owner=self.company, created_by=self.user,
            purchased_product=self.purchased_product)
        request = Request.objects.get()
        self.view_kwargs = {'pk': request.pk}
        self.assertFalse(request.action_taken)
        self.assertFalse(self.job.is_approved)

    def test_purchasedjob_accept(self):
        self.client.get(reverse('approve_admin_request',
                                kwargs=self.view_kwargs),
                        HTTP_HOST='test.jobs')

        request = Request.objects.get()
        job = PurchasedJob.objects.get()
        self.assertTrue(request.action_taken)
        self.assertTrue(job.is_approved)

    def test_purchasedjob_deny(self):
        self.client.get(reverse('deny_admin_request',
                                kwargs=self.view_kwargs),
                                HTTP_HOST='test.jobs')

        request = Request.objects.get()
        job = PurchasedJob.objects.get()
        self.assertTrue(request.action_taken)
        self.assertFalse(job.is_approved)

    def test_purchasedjob_block(self):
        self.client.get(reverse('block_admin_request',
                                kwargs=self.view_kwargs),
                        HTTP_HOST='test.jobs')

        request = Request.objects.get()
        job = PurchasedJob.objects.get()
        self.assertTrue(request.action_taken)
        self.assertFalse(job.is_approved)
        company = Company.objects.get(pk=self.company.pk)
        self.assertTrue(self.user in company.companyprofile.blocked_users.all())
        response = self.client.get(reverse('purchasedjob_add',
                                           kwargs={'product': self.product.pk}))
        self.assertEqual(response.status_code, 404)

    def test_unblock_user(self):
        response = self.client.get(reverse('blocked_user_management'))
        self.assertTrue("You currently have not blocked any users"
                        in response.content)
        profile = CompanyProfile.objects.get(company=self.company)
        self.assertFalse(self.user in profile.blocked_users.all())

        profile.blocked_users.add(self.user)
        response = self.client.get(reverse('blocked_user_management'))
        contents = BeautifulSoup(response.content)
        emails = contents.select('td.blocked_user-blocked_user-email')
        self.assertEqual(self.user.email,
                         emails[0].text)

        unblock_href = contents.select('td.blocked_user-actions')[0]
        unblock_href = unblock_href.select('a')[0].attrs['href']
        self.client.get(unblock_href)
        self.assertFalse(self.user in profile.blocked_users.all())

    def test_blocked_user_sees_modal(self):
        profile = CompanyProfile.objects.create(company=self.company)
        profile.blocked_users.add(self.user)
        add_job_link = reverse('purchasedjob_add',
                               args=[self.purchased_product.pk])
        for url in [reverse('purchasedjobs_overview',
                            args=[self.purchased_product.pk])]:
            response = self.client.get(url, HTTP_HOST='test.jobs')
            self.assertFalse(add_job_link in response.content)
            self.assertTrue('id="block-modal"' in response.content)
