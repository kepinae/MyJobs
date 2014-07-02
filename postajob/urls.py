from django.conf.urls import *

from postajob import views

urlpatterns = patterns(
    '',

    # Views for job and admin
    url(r'^order/',
        views.order_postajob,
        name="order_postajob"),
    url(r'^companyuser/',
        views.is_company_user,
        name="is_company_user"),

    # Posted job management
    url(r'^jobs/$',
        views.jobs_overview,
        name='jobs_overview'),

    # Purchased job management
    url(r'^purchased/jobs/$',
        views.purchasedjobs_overview,
        name='purchasedjobs_overview'),

    # Purchased microsite management
    url(r'^admin/$',
        views.admin_overview,
        name='admin_overview'),

    # Job
    url(r'^job/add/',
        views.JobFormView.as_view(),
        name='job_add'),
    url(r'^job/delete/(?P<pk>\d+)/',
        views.JobFormView.as_view(),
        name='job_delete'),
    url(r'^job/update/(?P<pk>\d+)/',
        views.JobFormView.as_view(),
        name='job_update'),

    # PurchasedJob
    url(r'^job/purchase/add/(?P<product>\d+)/',
        views.PurchasedJobFormView.as_view(),
        name='purchasedjob_add'),
    url(r'^job/purchase/delete/(?P<pk>\d+)/',
        views.PurchasedJobFormView.as_view(),
        name='purchasedjob_update'),
    url(r'^job/purchase/update/(?P<pk>\d+)/',
        views.PurchasedJobFormView.as_view(),
        name='purchasedjob_delete'),

    # Product management
    url(r'^admin/product/$',
        views.admin_products,
        name='product'),
    url(r'^admin/product/add/',
        views.ProductFormView.as_view(),
        name='product_add'),
    url(r'^admin/product/delete/(?P<pk>\d+)/',
        views.ProductFormView.as_view(),
        name='product_delete'),
    url(r'^admin/product/update/(?P<pk>\d+)/',
        views.ProductFormView.as_view(),
        name='product_update'),

    # ProductGrouping
    url(r'^admin/product/group/$',
        views.admin_groupings,
        name='productgrouping'),
    url(r'^admin/product/group/add/',
        views.ProductGroupingFormView.as_view(),
        name='productgrouping_add'),
    url(r'^admin/product/group/delete/(?P<pk>\d+)/',
        views.ProductGroupingFormView.as_view(),
        name='productgrouping_delete'),
    url(r'^admin/product/group/update/(?P<pk>\d+)/',
        views.ProductGroupingFormView.as_view(),
        name='productgrouping_update'),

    # Offline Purchases
    url(r'^admin/purchase/offline/$',
        views.admin_offlinepurchase,
        name='offlinepurchase'),
    url(r'^admin/purchase/offline/add/',
        views.OfflinePurchaseFormView.as_view(),
        name='offlinepurchase_add'),
    url(r'^admin/purchase/offline/delete/(?P<pk>\d+)/',
        views.OfflinePurchaseFormView.as_view(),
        name='offlinepurchase_delete'),
    url(r'^admin/purchase/offline/update/(?P<pk>\d+)/',
        views.OfflinePurchaseFormView.as_view(),
        name='offlinepurchase_update'),

    # PurchasedProduct
    url(r'^product/purchase/add/(?P<product>\d+)/',
        views.PurchasedProductFormView.as_view(),
        name='purchasedproduct_add'),
    url(r'^product/purchase/delete/(?P<pk>\d+)/',
        views.PurchasedProductFormView.as_view(),
        name='purchasedproduct_delete'),
    url(r'^product/purchase/update/(?P<pk>\d+)/',
        views.PurchasedProductFormView.as_view(),
        name='purchasedproduct_update'),
)
