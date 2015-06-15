import operator
from slugify import slugify

from django.conf import settings
from django.contrib.auth.models import Group
from django.contrib.contenttypes import generic
from django.contrib.flatpages.models import FlatPage
from django.contrib.sites.models import Site
from django.contrib.syndication.views import Feed
from django.core.cache import cache
from django.core.validators import MaxValueValidator, ValidationError
from django.db import models
from django.db.models.query import QuerySet
from django.db.models.signals import post_delete, pre_delete, post_save
from django.dispatch import receiver

from haystack.inputs import Raw
from haystack.query import SQ

from saved_search.models import BaseSavedSearch, SOLR_ESCAPE_CHARS
from taggit.managers import TaggableManager

from moc_coding import models as moc_models
from registration.models import Invitation
from social_links import models as social_models
from seo.search_backend import DESearchQuerySet
from myjobs.models import User
from mypartners.models import Tag
from universal.helpers import get_domain, get_object_or_none, has_mx_record


import decimal


class JobsByBuidManager(models.Manager):
    def get_query_set(self):
        queryset = super(JobsByBuidManager, self).get_query_set()
        if settings.SITE_BUIDS:
            return queryset.filter(buid__in=settings.SITE_BUIDS)
        else:
            return queryset


class ConfigBySiteManager(models.Manager):
    def get_query_set(self):
        return super(ConfigBySiteManager, self).get_query_set().filter(
            seosite__id=settings.SITE_ID)


class GoogleAnalyticsBySiteManager(models.Manager):
    def get_query_set(self):
        return super(GoogleAnalyticsBySiteManager, self).get_query_set().filter(
            seosite__id=settings.SITE_ID)


def term_splitter(terms):
    """
    Splits strings representing multiple terms into lists
    :Inputs:
        terms: An dictionary of field:values, where values is iterable
    :Returns:
        A dictionary of field:values, where each item in values has been split
        according to its deliminter

    """
    sep = settings.FACET_RULE_DELIMITER
    results = {}
    for field in ('city', 'title', 'country', 'state'):
        try:
            results[field] = []
            for term_string in terms[field]:
                results[field].extend(term_string.split(sep))
            terms[field] = results[field]
        except AttributeError:
           terms[field] = []

    try:
        for onet_string in terms['onet']:
            results[field].extend(term_string.split(','))
        terms['onet'] = terms['onet']
    except AttributeError:
        terms['onet'] = []
    return terms


def sq_from_terms(terms):
    """
    Create a SearchQuery() object based on a dictionary of field:values
    Each of these values will be an iterable (consult saved_search.models module for
    illustration).

    Inputs:
    :results: A list of term dictionaries in the form {field_name: search_values}

    Returns:
    A SearchQuery() object for CustomFacet

    """
    results = []
    terms = term_splitter(terms)
    #First we build an SQ for each term, then we join them into a single SQ
    for attr,vals in terms.items():
        sq_attr = CustomFacet.field_to_solr_terms.get(attr, attr)
        if vals is None:
            continue;
        elif attr == 'querystring' and len(vals) > 0:
            #Query string is a raw query
            results.append(SQ(content=Raw(vals[0])))
        elif any(vals):
            #Build an SQ that joins non empty items in vals with boolean or
            filt = reduce(operator.or_,
                          [SQ((u"%s__exact" % sq_attr, i)) for i in vals if i])
            results.append(filt)

    if results:
        #Build a SQ that joins each non empty SQ in results with boolean and
        retval = reduce(operator.and_, filter(lambda x: x, results))
    else:
        retval = SQ()
    return retval


class Redirect(models.Model):
    """
    Contains most of the information required to determine how a url
    is to be transformed
    """
    guid = models.CharField(max_length=38, primary_key=True,
                            help_text='36-character hex string')
    buid = models.IntegerField(default=0,
                               help_text='Business unit ID for a given '
                                         'job provider')
    uid = models.IntegerField(unique=True, blank=True, null=True,
                              help_text="Unique id on partner's ATS or "
                                        "other job repository")
    url = models.TextField(help_text='URL being manipulated')
    new_date = models.DateTimeField(help_text='Date that this job was '
                                              'added')
    expired_date = models.DateTimeField(blank=True, null=True,
                                        help_text='Date that this job was '
                                                  'marked as expired')
    job_location = models.CharField(max_length=255, blank=True)
    job_title = models.CharField(max_length=255, blank=True)
    company_name = models.TextField(blank=True)

    class Meta:
        db_table = 'redirect_redirect'

    def __unicode__(self):
        return u'%s for guid %s' % (self.url, self.guid)

    def make_link(self):
        """Generates the redirected link for a redirect object."""
        # Handle the fact that guid is has leading/trailing braces and dashes.
        # '{XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX}'
        return "http://my.jobs/%s" % self.guid[1:-1].replace('-', '') + '10'


class CustomFacetQuerySet(QuerySet):
    def prod_facets_for_current_site(self):
        kwargs = {
            'seositefacet__seosite__id': settings.SITE_ID,
            'show_production': 1,
        }
        return self.filter(**kwargs)


class CustomFacetManager(models.Manager):
    def get_query_set(self):
        return CustomFacetQuerySet(self.model)

    def __getattr__(self, attr, *args):
        if attr.startswith("__"):
            raise AttributeError
        return getattr(self.get_query_set(), attr, *args)


class CustomFacet(BaseSavedSearch):
    """
    Stores search parameters as attributes and builds DESearchQuerySets

    Each CustomFacet object has a foreign key to an SeoSite object. This
    means that in order to create the same saved search across many SEO
    sites, the user will have to copy the saved search once for each site.

    This is made a bit easier by setting save_as == True in the ModelAdmin
    for this model. This allows the user to change the SEO site from the
    FK drop-down, then click "Save as New" to create a new Saved Search
    instance.

    """
    group = models.ForeignKey(Group, blank=True, null=True)
    business_units = models.ManyToManyField('BusinessUnit', blank=True,
                                            null=True)
    country = models.CharField(max_length=800, null=True, blank=True)
    state = models.CharField(max_length=800, null=True, blank=True)
    city = models.CharField(max_length=800, null=True, blank=True)
    keyword = TaggableManager()
    company = models.CharField(max_length=800, null=True, blank=True)
    onet = models.CharField(max_length=10, null=True, blank=True)
    always_show = models.BooleanField("Show With or Without Results",
                                      default=False)

    #Final querystring to send to solr. Updates when object is saved.
    saved_querystring = models.CharField(max_length=10000, blank=True)

    objects = CustomFacetManager()

    field_to_solr_terms = {'title': 'title',
                           'business_units__id': 'buid',
                           'country': 'country',
                           'state': 'state',
                           'onet': 'onet',
                           'keyword__name': 'text',
                           'city': 'location_exact'}

    def __unicode__(self):
        return '%s' % self.name

    def active_site_facet(self):
        facets = self.seositefacet_set.filter(seosite__id=settings.SITE_ID)
        return facets.first()

    def get_op(self):
        """
        Returns boolean operation from active site facet.

        The boolean_operation is currently set in middleware. If it's not set,
        then it's possible that the wrong operation will be returned if there
        are multiple site facets for the active site and they have different
        operations.

        """
        return getattr(self, 'boolean_operation',
                       self.active_site_facet().boolean_operation)

    def clean(self):
        if not self.pk:
            self.save()
        self.name_slug = slugify(self.name)
        self.url_slab = '%s/new-jobs::%s' % (self.name_slug, self.name)
        self.save()

    def save(self, *args, **kwargs):
        if self.querystring:
            sqs = DESearchQuerySet().using('default')
            fail_status = sqs.query.backend.silently_fail
            sqs.query.backend.silently_fail = False

            try:
                sqs.narrow(self.querystring).query.get_results()
            except:
                sqs.query.backend.silently_fail = fail_status
                raise ValidationError("Invalid raw lucene query")

            sqs.query.backend.silently_fail = fail_status

        if not self.pk:
            super(CustomFacet, self).save(*args, **kwargs)

        sqs = DESearchQuerySet().filter(self.create_sq())
        self.saved_querystring = sqs.query.build_query()
        super(CustomFacet, self).save()

    def _attr_dict(self):
        # Any new additions to the custom field that will be searched on must
        # be added to the return value of this method.

        sep = settings.FACET_RULE_DELIMITER
        kw = self.keyword.all()
        cities = [i for i in self.city.split(sep)]

        try:
            onets = self.onet.split(',')
        except AttributeError:
            onets = []
        return {'title': [i for i in self.title.split(sep)],
                'buid': self.business_units.all().values_list('id', flat=True),
                'country': [i for i in self.country.split(sep)],
                'state': [i for i in self.state.split(sep)],
                'onet': onets,
                'text': kw.values_list('name', flat=True) or u'',
                'location_exact': cities}

    def create_sq(self):
        results = []
        for attr, val in self._attr_dict().items():
            if any(val):
                #Build an SQ that joins non empty items in val with boolean or
                filt = reduce(operator.or_,
                              [SQ((u"%s__exact" % attr, i)) for i in val if i])
                results.append(filt)
        if self.querystring:
            results.append(SQ(content=Raw(self.querystring)))

        if results:
            #Build a SQ that joins each non empty SQ in results with boolean and
            retval = reduce(operator.and_, filter(lambda x: x, results))
        else:
            retval = SQ()
        return retval

    def get_sqs(self):
        """
        Returns the DESearchQuerySet object generated by self._attrd_ictionary
        when passed to the Solr backend.

        Warning, do not use for a set of custom facets, it will create a
        database hit for each object. Use .create_sq() directly on the queryset
        instead. We're keeping this method for admin use only.

        """
        attr_dict = self._attr_dict()
        bu = [s.business_units.all() for s in self.sites.all()]
        filts = []
        if bu:
            bu = ','.join(set([str(b.id) for b in reduce(lambda x, y: x | y, bu)]))

        sqs = DESearchQuerySet().models(jobListing).narrow(self._make_qs('buid', bu))

        for attr, val in attr_dict.items():
            if any(val):
                filt = reduce(operator.or_,
                              [SQ(("%s__exact" % attr, i)) for i in val if i])
                filts.append(filt)

        if filts:
            q_filter = reduce(operator.and_, filts)
            sqs = sqs.filter(q_filter)

        return sqs

    def _escape(self, param):
        for c in SOLR_ESCAPE_CHARS:
            param = param.replace(c, '')
        param = param.replace(':', '\\:')
        return param

    def _make_qs(self, field, params):
        """
        Generates the query string which will be passed to Solr directly.

        """
        # If no parameter was passed in, immediately dump back out.
        if not params:
            return ''

        params = params.split(',')
        qs = []
        joinstring = ' OR '

        for thing in params:
            qs.append('%s:%s' % (field, self._escape(thing)))

        return joinstring.join(qs)


@receiver(post_save, sender=CustomFacet)
@receiver(pre_delete, sender=CustomFacet)
def clear_page_cache(sender, **kwargs):
    """
    Clear cache for given domains after CustomFacet object is changed
    in some way.

    """
    # Can't put this in models.py since importing CustomFacet creates a
    # circular import condition.
    obj = kwargs['instance']

    if not obj.seosite_set.exists():
        return

    configs = Configuration.objects.filter(seosite__facets=obj).distinct()

    for config in configs:
        config.save()


class jobListing (models.Model):
    def __unicode__(self):
        return self.title

    class Meta:
        verbose_name = 'Job Listing'
        verbose_name_plural = 'Job Listings'

    city = models.CharField(max_length=200, blank=True, null=True)
    citySlug = models.SlugField(blank=True, null=True)
    country = models.CharField(max_length=200, blank=True, null=True)
    countrySlug = models.SlugField(blank=True, null=True)
    country_short = models.CharField(max_length=3, blank=True, null=True,
                                     db_index=True)
    date_new = models.DateTimeField('date new')
    date_updated = models.DateTimeField('date updated')
    description = models.TextField()
    hitkey = models.CharField(max_length=50)
    link = models.URLField(max_length=200)
    location = models.CharField(max_length=200, blank=True, null=True)
    reqid = models.CharField(max_length=50, blank=True, null=True)
    state = models.CharField(max_length=200, blank=True, null=True)
    stateSlug = models.SlugField(blank=True, null=True)
    state_short = models.CharField(max_length=3, blank=True, null=True)
    title = models.CharField(max_length=200)
    titleSlug = models.SlugField(max_length=200, blank=True, null=True,
                                 db_index=True)
    uid = models.IntegerField(db_index=True, unique=True)
    zipcode = models.CharField(max_length=15, null=True, blank=True)

    objects = models.Manager()
    this_site = JobsByBuidManager()

    def return_id(self):
        return self.id

    def save(self):
        self.titleSlug = slugify(self.title)
        self.countrySlug = slugify(self.country)
        self.stateSlug = slugify(self.state)
        self.citySlug = slugify(self.city)

        if self.city and self.state_short:
            self.location = self.city + ', ' + self.state_short
        elif self.city and self.country_short:
            self.location = self.city + ', ' + self.country_short
        elif self.state and self.country_short:
            self.location = self.state + ', ' + self.country_short
        elif self.country:
            self.location = 'Virtual, ' + self.country_short
        else:
            self.location = 'Global'

        super(jobListing, self).save()


class SeoSite(Site):
    class Meta:
        verbose_name = 'Seo Site'
        verbose_name_plural = 'Seo Sites'

    def associated_companies(self):
        buids = self.business_units.all()
        return Company.objects.filter(job_source_ids__id__in=buids)

    def network_sites(self):
        return SeoSite.objects.filter(site_tags__site_tag='network')

    def network_sites_and_this_site(self):
        query = models.Q(site_tags__site_tag='network') | models.Q(id=self.id)
        return SeoSite.objects.filter(query)

    def this_site_only(self):
        # This should return self, but I really want to stay consistent and
        # return a QuerySet so that all the functions can be used
        # identically without knowing the value of postajob_filter_type.
        return SeoSite.objects.filter(id=self.id)

    def company_sites(self):
        companies = self.associated_companies()
        company_buids = companies.values_list('job_source_ids', flat=True)

        sites = SeoSite.objects.filter(business_units__id__in=company_buids)
        return sites.exclude(site_tags__site_tag='network')

    def network_and_company_sites(self):
        companies = self.associated_companies()
        company_buids = companies.values_list('job_source_ids', flat=True)

        query = [models.Q(business_units__id__in=company_buids),
                 models.Q(site_tags__site_tag='network')]

        return SeoSite.objects.filter(reduce(operator.or_, query))

    def all_sites(self):
        return SeoSite.objects.all()

    postajob_filter_options_dict = {
        'network sites only': network_sites,
        'network sites and this site': network_sites_and_this_site,
        'this site only': this_site_only,
        'network sites and sites associated '
        'with the company that owns this site': network_and_company_sites,
        'sites associated with the company that owns this site': company_sites,
        'all sites': all_sites,
    }
    postajob_filter_options = tuple([(k, k) for k in
                                     postajob_filter_options_dict.keys()])

    group = models.ForeignKey('auth.Group', null=True)
    facets = models.ManyToManyField('CustomFacet', null=True, blank=True,
                                    through='SeoSiteFacet')
    configurations = models.ManyToManyField('Configuration', blank=True)
    google_analytics = models.ManyToManyField('GoogleAnalytics', null=True,
                                              blank=True)
    business_units = models.ManyToManyField('BusinessUnit', null=True,
                                            blank=True)
    featured_companies = models.ManyToManyField('Company', null=True,
                                                blank=True)
    microsite_carousel = models.ForeignKey('social_links.MicrositeCarousel',
                                           null=True, blank=True,
                                           on_delete=models.SET_NULL)
    billboard_images = models.ManyToManyField('BillboardImage', blank=True,
                                              null=True)
    site_title = models.CharField('Site Title', max_length=200, blank=True,
                                  default='')
    site_heading = models.CharField('Site Heading', max_length=200, blank=True,
                                    default='')
    site_description = models.CharField('Site Description', max_length=200,
                                        blank=True, default='')
    google_analytics_campaigns = models.ForeignKey('GoogleAnalyticsCampaign',
                                                   null=True, blank=True)
    view_sources = models.ForeignKey('ViewSource', null=True, blank=True)
    ats_source_codes = models.ManyToManyField('ATSSourceCode', null=True,
                                              blank=True)
    special_commitments = models.ManyToManyField('SpecialCommitment',
                                                 blank=True, null=True)
    site_tags = models.ManyToManyField('SiteTag', blank=True, null=True)

    # The "designated" site package specific to this seosite.
    # This site should be the only site attached to site_package.
    site_package = models.ForeignKey('postajob.SitePackage', null=True,
                                     on_delete=models.SET_NULL)

    postajob_filter_type = models.CharField(max_length=255,
                                            choices=postajob_filter_options,
                                            default='this site only')
    canonical_company = models.ForeignKey('Company', blank=True, null=True,
                                          on_delete=models.SET_NULL,
                                          related_name='canonical_company_for')
    email_domain = models.CharField(max_length=255, default='my.jobs')

    def clean_email_domain(self):
        # TODO: Finish after MX Records are sorted out
        # Determine if the company actually has permission to use the domain.
        domains = self.canonical_company.get_seo_sites().values_list('domain',
                                                                     flat=True)
        domains = [get_domain(domain) for domain in domains]
        domains.append('my.jobs')
        if self.email_domain not in domains:
            raise ValidationError('You can only send emails from a domain '
                                  'that is associated with your company.')

        # Ensure that we have an MX record for the domain.
        if not has_mx_record(self.email_domain):
            raise ValidationError('You do not currently have the ability '
                                  'to send emails from this domain.')
        return self.email_domain

    def postajob_site_list(self):
        filter_function = self.postajob_filter_options_dict.get(
            self.postajob_filter_type, SeoSite.this_site_only)
        return filter_function(self)

    @staticmethod
    def clear_caches(sites):
        # Increment Configuration revision attributes, which is used
        # when calculating a custom_cache_pages cache key prefix.
        # This will effectively expire the page cache for custom_cache_page
        # views_
        configs = Configuration.objects.filter(seosite__in=sites)
        # https://docs.djangoproject.com/en/dev/topics/db/queries/#query-expressions
        configs.update(revision=models.F('revision') + 1)
        Configuration.clear_caches(configs)
        # Delete domain-based cache entries that don't use the
        # custom_cache_page prefix
        site_cache_keys = ['%s:SeoSite' % site.domain for site in sites]
        buid_cache_keys = ['%s:buids' % key for key in site_cache_keys]
        social_cache_keys = ['%s:social_links' % site.domain for site in sites]
        cache.delete_many(site_cache_keys + buid_cache_keys + social_cache_keys)


    def email_domain_choices(self,):
        from postajob.models import CompanyProfile
        profile = get_object_or_none(CompanyProfile,
                                     company=self.canonical_company)
        email_domain_field = SeoSite._meta.get_field('email_domain')
        choices = [
            (email_domain_field.get_default(), email_domain_field.get_default()),
            (self.domain, self.domain),
        ]
        if profile and profile.outgoing_email_domain:
            choices.append((profile.outgoing_email_domain,
                            profile.outgoing_email_domain))
        return choices

    def save(self, *args, **kwargs):
        super(SeoSite, self).save(*args, **kwargs)
        self.clear_caches([self])

    def user_has_access(self, user):
        """
        In order for a user to have access they must be a CompanyUser
        for the Company that owns the SeoSite.
        """
        site_buids = self.business_units.all()
        companies = Company.objects.filter(job_source_ids__in=site_buids)
        user_companies = user.get_companies()
        for company in companies:
            if company not in user_companies:
                return False
        return True

    def get_companies(self):
        site_buids = self.business_units.all()
        return Company.objects.filter(job_source_ids__in=site_buids).distinct()


class SeoSiteFacet(models.Model):
    """This model defines the default Custom Facet(s) for a given site."""
    STANDARD = 'STD'
    DEFAULT = 'DFT'
    FEATURED = 'FTD'
    FACET_TYPE_CHOICES = ((STANDARD, 'Standard'), (DEFAULT, 'Default'),
                          (FEATURED, 'Featured'), )

    BOOLEAN_CHOICES = (('or', 'OR'), ('and', 'AND'), )

    FACET_GROUP_CHOICES = ((1, 'Facet Group 1'), (2, 'Facet Group 2'),
                           (3, 'Facet Group 3'), )

    facet_group = models.IntegerField(choices=FACET_GROUP_CHOICES, default=1)
    seosite = models.ForeignKey('SeoSite', verbose_name="Seo Site")
    customfacet = models.ForeignKey('CustomFacet', verbose_name="Custom Facet")
    facet_type = models.CharField(max_length=4,
                                  choices=FACET_TYPE_CHOICES,
                                  default=STANDARD,
                                  verbose_name="Facet Type",
                                  db_index=True)
    boolean_operation = models.CharField(max_length=3,
                                         default='or',
                                         choices=BOOLEAN_CHOICES,
                                         verbose_name="Boolean Operation",
                                         db_index=True)
    boolean_choices = ['or', 'and']

    class Meta:
        verbose_name = "Seo Site Facet"
        verbose_name_plural = "Seo Site Facets"


class Company(models.Model):
    """
    This model defines companies that come from various job sources (currently
    business units).

    """
    def __unicode__(self):
        return self.name

    natural_key = __unicode__

    class Meta:
        verbose_name = 'Company'
        verbose_name_plural = 'Companies'
        ordering = ['name']
        unique_together = ('name', 'user_created')

    def save(self, *args, **kwargs):
        exists = str(self.pk).isdigit()

        self.company_slug = slugify(self.name)
        super(Company, self).save(*args, **kwargs)

        if not exists:
            default_tags = [
                {"name": "Veteran", "hex_color": "5EB94E"},
                {"name": "Female", "hex_color": "4BB1CF"},
                {"name": "Minority", "hex_color": "FAA732"},
                {"name": "Disability", "hex_color": "808A9A"},
                {"name": "Disabled Veteran", "hex_color": "659274"}
            ]
            for tag in default_tags:
                Tag.objects.get_or_create(company=self, **tag)

    def associated_jobs(self):
        b_units = self.job_source_ids.all()
        job_count = 0
        for unit in b_units:
            job_count += unit.associated_jobs
        return job_count

    def featured_on(self):
        return ", ".join(self.seosite_set.all().values_list("domain",
                                                            flat=True))

    @property
    def company_user_count(self):
        """
        Counts how many users are mapped to this company. This is useful for
        determining which company to map companyusers to when two company
        instances have very similar names.
        
        It is treated as a property of the model.
        
        """
        return self.companyuser_set.count()
        
    admins = models.ManyToManyField(User, through='CompanyUser')
    name = models.CharField('Name', max_length=200)
    company_slug = models.SlugField('Company Slug', max_length=200, null=True,
                                    blank=True)
    job_source_ids = models.ManyToManyField('BusinessUnit')
    logo_url = models.URLField('Logo URL', max_length=200, null=True,
                               blank=True, help_text="The url for the 100x50 "
                               "logo image for this company.")
    linkedin_id = models.CharField('LinkedIn Company ID',
                                   max_length=20, null=True, blank=True,
                                   help_text="The LinkedIn issued company "
                                   "ID for this company.")
    og_img = models.URLField('Open Graph Image URL', max_length=200, null=True,
                             blank=True, help_text="The url for the large "
                             "format logo for use when sharing jobs on "
                             "LinkedIn, and other social platforms that support"
                             " OpenGraph.")
    canonical_microsite = models.URLField('Canonical Microsite URL',
                                          max_length=200, null=True, blank=True,
                                          help_text="The primary "
                                          "directemployers microsite for this "
                                          "company.")
    member = models.BooleanField('DirectEmployers Association Member',
                                 default=False)
    social_links = generic.GenericRelation(social_models.SocialLink,
                                           object_id_field='id',
                                           content_type_field='content_type')
    digital_strategies_customer = models.BooleanField(
        'Digital Strategies Customer', default=False)
    enhanced = models.BooleanField('Enhanced', default=False)
    site_package = models.ForeignKey('postajob.SitePackage', null=True,
                                     on_delete=models.SET_NULL)

    prm_saved_search_sites = models.ManyToManyField('SeoSite', null=True,
                                                    blank=True)

    # Permissions
    prm_access = models.BooleanField(default=True)
    product_access = models.BooleanField(default=False)
    posting_access = models.BooleanField(default=False)
    user_created = models.BooleanField(default=False)

    def slugified_name(self):
        return slugify(self.name)

    def get_seo_sites(self):
        """
        Retrieves a given company's microsites

        Inputs:
        :company: Company whose microsites are being retrieved

        Outputs:
        :microsites: List of microsites
        """
        buids = self.job_source_ids.all()

        microsites = SeoSite.objects.filter(models.Q(business_units__in=buids)
                                            | models.Q(canonical_company=self))
        return microsites

    def user_has_access(self, user):
        """
        In order for a user to have access they must be a CompanyUser
        for the Company.
        """
        return user in self.admins.all()

    @property
    def has_packages(self):
        return self.sitepackage_set.filter(
            sites__in=settings.SITE.postajob_site_list()).exists()


class FeaturedCompany(models.Model):
    """
    Featured company option for a given multi-company SeoSite.
    """
    seosite = models.ForeignKey('SeoSite')
    company = models.ForeignKey('Company')
    is_featured = models.BooleanField('Featured Company?', default=False)


class SpecialCommitment(models.Model):
    """
    Special Commits are used on a site by site basis to place Schema.org
    tags on the site. This flags the site as containing jobs for a distinct
    set of job seekers.
    """
    name = models.CharField(max_length=200)
    commit = models.CharField(
        'Schema.org Commit Code',
        help_text="VeteranCommit, SummerCommit, etc...",
        max_length=200)

    def __unicode__(self):
        return self.name

    def committed_sites(self):
        return ", ".join(self.seosite_set.all().values_list("domain",
                                                            flat=True))

    class Meta:
        verbose_name = "Special Commitment"
        verbose_name_plural = "Special Commitments"


class GoogleAnalyticsCampaign(models.Model):
    """
    Defines a Google Analytics Campaign
    More Info:
    http://support.google.com/googleanalytics/bin/answer.py?hl=en&answer=55578

    If there is ever a need for a non-google analytics model, create a base
    class for this model first.
    """
    name = models.CharField(max_length=200, default='')
    group = models.ForeignKey('auth.group', null=True)
    campaign_source = models.CharField(
        help_text=" (referrer: google, citysearch, newsletter4)",
        max_length=200, default='')
    campaign_medium = models.CharField(
        help_text=" (marketing medium: cpc, banner, email)",
        max_length=200, default='')
    campaign_name = models.CharField(
        help_text="(product, promo code, or slogan)",
        max_length=200, default='')
    campaign_term = models.CharField(
        help_text="(identify the paid keywords)",
        max_length=200, default='')
    campaign_content = models.CharField(
        help_text="(use to differentiate ads)",
        max_length=200, default='')

    def __unicode__(self):
        return "Google Analytics Campaign - %s" % self.campaign_name

    def sites(self):
        return ", ".join(self.seosite_set.all().values_list("domain",
                                                            flat=True))

    class Meta:
        verbose_name = "Google Analytics Campaign"
        verbose_name_plural = "Google Analytics Campaigns"


class URINameValuePair(models.Model):
    """
    Create a name value pair for use on a URL
    """
    name = models.CharField(max_length=200, default='')
    value= models.CharField(max_length=200, default='')
    group = models.ForeignKey('auth.group', null=True)

    def __unicode__(self):
        return "%s=%s" % (self.name, self.value)

    class Meta:
        abstract = True


class ATSSourceCode(URINameValuePair):
    """
    Instance of URINameValuePairmodel for tracking a specific ATS source code
    """
    ats_name = models.CharField(max_length=200,default='')

    def sites(self):
        return ", ".join(self.seosite_set.all().values_list("domain",
                                                            flat=True))

    class Meta:
        verbose_name = 'ATS Source Code'


class ViewSource(models.Model):
    """
    Defines a source code to override the default provided by the job source
    """
    name = models.CharField(max_length=200, default='')
    view_source = models.IntegerField(max_length=20, default='')

    def __unicode__(self):
        return "%s (%s)" % (self.name, self.view_source)

    def sites(self):
        return ", ".join(self.seosite_set.all().values_list("domain",
                                                            flat=True))

    class Meta:
        verbose_name = "View Source"
        verbose_name_plural = "View Sources"


class BillboardImage(models.Model):
    def __unicode__(self):
        return "%s: %s" % (self.title, str(self.id))

    title = models.CharField('Title', max_length=200)
    group = models.ForeignKey('auth.group', null=True)
    image_url = models.URLField('Image URL', max_length=200)
    copyright_info = models.CharField('Copyright Info', max_length=200)
    source_url = models.URLField('Source URL', max_length=200)
    logo_url = models.URLField('Logo Image URL',
                               max_length=200, null=True, blank=True)
    sponsor_url = models.URLField('Logo Sponsor URL',
                                  max_length=200, null=True, blank=True)

    class Meta:
        verbose_name = 'Billboard Image'
        verbose_name_plural = 'Billboard Images'

    def on_sites(self):
        return ", ".join(self.seosite_set.all().values_list("domain",
                                                            flat=True))

    def number_of_hotspots(self):
        return self.billboardhotspot_set.all().count()

    def has_hotspots(self):
        # returns True if the the billboard has hotspots.
        return self.number_of_hotspots() > 0
    has_hotspots.boolean = True


class BillboardHotspot(models.Model):
    billboard_image = models.ForeignKey(BillboardImage)
    title = models.CharField('Title', max_length=50,
                             help_text="Max 50 characters")
    text = models.CharField('Text', max_length=140,
                            help_text="Max 140 characters.  "
                                      "Use HTML markup for line breaks "
                                      "and formatting.")
    url = models.URLField('URL', null=True, blank=True)
    display_url = models.TextField('Display URL', null=True, blank=True)
    offset_x = models.IntegerField('Offset X')
    offset_y = models.IntegerField('Offset Y')
    primary_color = models.CharField('Primary Color', max_length=6,
                                     default='5A6D81')
    font_color = models.CharField('Font Color', max_length=6, default='FFFFFF')
    border_color = models.CharField('Border Color', max_length=6,
                                    default='FFFFFF')

    class Meta:
        verbose_name = 'Billboard Hotspot'


class SiteTag(models.Model):
    """
    Defines a tag to help categorize SeoSites. These tags will allow us to
    arbitrarily group different kinds of sites (members, companies,
    network sites, etc.)
    """
    site_tag = models.CharField('Site Tag', max_length=100, unique=True)
    tag_navigation = models.BooleanField('Tag can be used for navigation',
                                         default=False,
                                         help_text='Tag can be used for '
                                                   'navigation by users. '
                                                   'Viewable by public.')
    is_site_family = models.BooleanField('Tag represents site family',
                                         default=False,
                                         help_text='Site tag represents '
                                                   'a family of sites.')
    parent = models.ForeignKey(SeoSite, blank=True, null=True,
                               help_text='The parent site if the tag is a '
                                         'for a site family.')

    def __unicode__(self):
        return "%s" % self.site_tag

    class Meta:
        verbose_name = 'Site Tag'


class SeoSiteRedirect(models.Model):
    redirect_url = models.CharField('domain name', max_length=100,
                                    db_index=True)
    seosite = models.ForeignKey(SeoSite)

    class Meta:
        unique_together = ["redirect_url", "seosite"]
        verbose_name = 'Seo Site Redirect'
        verbose_name_plural = 'Seo Site Redirects'


class Configuration(models.Model):
    ORDER_CHOICES = (
        (1, 1),
        (2, 2),
        (3, 3),
        (4, 4),
        (5, 5),
        (6, 6),
        (7, 7),
        (8, 8),
        (9, 9),
    )

    STATUS_CHOICES = (
        (1, 'Staging'),
        (2, 'Production'),
    )

    HOME_ICON_CHOICES = (
        (1, 'None'),
        (2, 'Bottom'),
        (3, 'Top')
    )

    def __init__(self, *args, **kwargs):
        super(Configuration, self).__init__(*args, **kwargs)
        self._original_browse_moc_show = self.browse_moc_show
        self.browse_mapped_moc_show = self.browse_moc_show
        self.browse_mapped_moc_text = self.browse_moc_text
        self.browse_mapped_moc_order = self.browse_moc_order

    @staticmethod
    def clear_caches(configs):
        # Delete all cached configurations used to determine cache key prefixes
        # in directseo.seo.decorators.custom_cache_page because the
        # configuration revision referenced in the key_prefix has changed.
        sites = SeoSite.objects.filter(configurations__in=configs)
        statuses = set()
        for config in configs:
            statuses.add(config.status)
        for status in statuses:
            cache.delete_many(["%s:config:%s" % (site.domain, status) for
                               site in sites.all()])
            cache.delete_many(["jobs_count::%s" % site.pk for
                               site in  sites.all()])

    def clear_cache(self):
        self.clear_caches([self])

    def save(self, *args, **kwargs):
        # Increment the revision number so a new cache key will be used for urls
        # of the seosites linked to this configuration.
        self.revision += 1
        super(Configuration, self).save(*args, **kwargs)
        self.clear_caches([self])

    def status_title(self):
        if self.status == 1:
            status_title = 'Staging'
        elif self.status == 2:
            status_title = 'Production'
        else:
            status_title = 'Pending'
        return status_title

    def __unicode__(self):
        if self.title:
            return "%s -- %s rev.%s" % (self.title, self.status_title(),
                                        str(self.id))
        else:
            return "%s: rev.%s" % (self.status_title(), str(self.id))

    def show_sites(self):
        return ", ".join(self.seosite_set.all().values_list("domain",
                                                            flat=True))

    title = models.CharField(max_length=50, null=True)
    # version control
    status = models.IntegerField('Status', default=1, choices=STATUS_CHOICES,
                                 null=True, blank=True, db_index=True)
    # navigation section
    defaultBlurb = models.TextField('Blurb Text', blank=True, null=True)
    defaultBlurbTitle = models.CharField('Blurb Title', max_length=100,
                                         blank=True, null=True)
    #default_blurb_always_show = models.BooleanField('Always Show',
    #                                                default=False)
    browse_country_show = models.BooleanField('Show', default=True)
    browse_state_show = models.BooleanField('Show', default=True)
    browse_city_show = models.BooleanField('Show', default=True)
    browse_title_show = models.BooleanField('Show', default=True)
    browse_facet_show = models.BooleanField('Show', default=False)
    browse_facet_show_2 = models.BooleanField('Show', default=False)
    browse_facet_show_3 = models.BooleanField('Show', default=False)
    browse_moc_show = models.BooleanField('Show', default=False)
    browse_company_show = models.BooleanField('Show', default=False)

    browse_country_text = models.CharField('Heading for Country Facet',
                                           default='Country',
                                           max_length=50)
    browse_state_text = models.CharField('Heading for State Facet',
                                         default='State',
                                         max_length=50)
    browse_city_text = models.CharField('Heading for City Facet',
                                        default='City',
                                        max_length=50)
    browse_title_text = models.CharField('Heading for Title Facet',
                                         default='Title',
                                         max_length=50)
    browse_facet_text = models.CharField('Heading for Custom Facet Group 1',
                                         default='Job Profiles',
                                         max_length=50)
    browse_facet_text_2 = models.CharField('Heading for Custom Facet Group 2',
                                           default='Job Profiles',
                                           max_length=50)
    browse_facet_text_3 = models.CharField('Heading for Custom Facet Group 3',
                                           default='Job Profiles',
                                           max_length=50)
    browse_moc_text = models.CharField('Heading for MOC Facet',
                                       default='Military Titles',
                                       max_length=50)
    browse_company_text = models.CharField('Heading for Company Facet',
                                           default='Company',
                                           max_length=50)

    browse_country_order = models.IntegerField('Order', default=3,
                                               choices=ORDER_CHOICES)
    browse_state_order = models.IntegerField('Order', default=4,
                                             choices=ORDER_CHOICES)
    browse_city_order = models.IntegerField('Order', default=5,
                                            choices=ORDER_CHOICES)
    browse_title_order = models.IntegerField('Order', default=6,
                                             choices=ORDER_CHOICES)
    browse_facet_order = models.IntegerField('Order', default=2,
                                             choices=ORDER_CHOICES)
    browse_facet_order_2 = models.IntegerField('Order', default=2,
                                               choices=ORDER_CHOICES)
    browse_facet_order_3 = models.IntegerField('Order', default=2,
                                               choices=ORDER_CHOICES)
    browse_moc_order = models.IntegerField('Order', default=1,
                                           choices=ORDER_CHOICES)
    browse_company_order = models.IntegerField('Order', default=7,
                                               choices=ORDER_CHOICES)
    num_subnav_items_to_show = models.IntegerField('Subnav Options Shown',
                                                   default=9)
    num_filter_items_to_show = models.IntegerField('Filter Options Shown',
                                                   default=10)
    num_job_items_to_show = models.IntegerField('Job Listings Shown',
                                                default=15)
    # url options
    location_tag = models.CharField(max_length=50, default='jobs')
    title_tag = models.CharField(max_length=50, default='jobs-in')
    facet_tag = models.CharField(max_length=50, default='new-jobs')
    moc_tag = models.CharField(max_length=50, default='vet-jobs')
    company_tag = models.CharField(max_length=50, default='careers')
    # template section
    meta = models.TextField(null=True, blank=True)
    wide_header = models.TextField(null=True, blank=True)
    header = models.TextField(null=True, blank=True)
    body = models.TextField('Custom Homepage Body', null=True, blank=True)
    wide_footer = models.TextField(null=True, blank=True)
    footer = models.TextField(null=True, blank=True)
    view_all_jobs_detail = models.BooleanField(
        'Use detailed "View All Jobs" label',
        help_text='Include site title details in "View All Jobs" link text',
        default=False)
    # site links
    directemployers_link = models.URLField(max_length=200,
                                           default='http://directemployers.org')
    show_social_footer = models.BooleanField('Show Social Footer', default=True,
                                             help_text='Include social footer '
                                                       'on job listing pages.')

    # stylesheet manytomany relationship
    backgroundColor = models.CharField(max_length=6, blank=True, null=True)
    fontColor = models.CharField(max_length=6, default='666666')
    primaryColor = models.CharField(max_length=6, default='990000')
    # manage authorization
    group = models.ForeignKey('auth.Group', null=True)
    # revision field for cache key decorator
    revision = models.IntegerField('Revision', default=1)

    # home page template settings
    home_page_template = models.CharField('Home Page Template', max_length=200,
                                          default='home_page/home_page_listing.html')
    show_home_microsite_carousel = models.BooleanField('Show Microsite Carousel'
                                                       ' on Home Page',
                                                       default=False)
    show_home_social_footer = models.BooleanField('Show Social Footer on'
                                                  ' Home Page',
                                                  default=False)
    publisher = models.CharField('Google plus page id', max_length=50,
                                 blank=True,
                                 help_text="Google plus page id for "
                                           "publisher tag")

    objects = models.Manager()
    this_site = ConfigBySiteManager()

    #Value from 0 to 1 showing what percent of featured jobs to display per page
    percent_featured = models.DecimalField(
        max_digits=3, decimal_places=2,
        default=decimal.Decimal('.5'),
        validators=[MaxValueValidator(decimal.Decimal('1.00'))],
        verbose_name="Featured Jobs Maximum Percentage")

    show_saved_search_widget = models.BooleanField(default=False,
                                                   help_text='Show saved '
                                                             'search widget '
                                                             'on job listing '
                                                             'page.')

    moc_label = models.CharField(max_length=255, blank=True)
    what_label = models.CharField(max_length=255, blank=True)
    where_label = models.CharField(max_length=255, blank=True)

    moc_placeholder = models.CharField(max_length=255, blank=True)
    what_placeholder = models.CharField(max_length=255, blank=True)
    where_placeholder = models.CharField(max_length=255, blank=True)

    moc_helptext = models.TextField(blank=True)
    what_helptext = models.TextField(blank=True)
    where_helptext = models.TextField(blank=True)


class GoogleAnalytics (models.Model):
    web_property_id = models.CharField('Web Property ID', max_length=20)
    group = models.ForeignKey('auth.Group', null=True)

    objects = models.Manager()
    this_site = GoogleAnalyticsBySiteManager()

    def show_sites(self):
        return ", ".join(self.seosite_set.all().values_list("domain",flat=True))

    class Meta:
        verbose_name = 'Google Analytics'
        verbose_name_plural = 'Google Analytics'

    def __unicode__(self):
        return self.web_property_id


class JobFeed(Feed):
    link = ""

    def __init__(self, type):
        self.type = type

    def item_title(self, item):
        # Creates a location description string from locations fields if
        # they exist
        loc_list = [item[key] for key in
            ['country_short', 'state_short', 'city'] if item.get(key)]
        title_loc = "-".join(loc_list)
        return "(%s) %s" % (title_loc, item['title'])

    def item_description(self, item):
        return item['description']

    def item_link(self, item):
        is_posted = item.get('is_posted', False)
        if is_posted:
            # If an item is posted, instead of using the
            # redirect link we use the http://site.jobs/guid/jobs/ link
            # that goes directly to the microsite.
            return "/%s/job/" % item['guid']

        else:
            vs = settings.FEED_VIEW_SOURCES.get(self.type, 20)
            return '/%s%s' % (item['guid'], vs)

    def item_pubdate(self, item):
        return item['date_new']


class BusinessUnit(models.Model):
    def __unicode__(self):
        return "%s: %s" % (self.title, str(self.id))

    class Meta:
        verbose_name = 'Business Unit'
        verbose_name_plural = 'Business Units'

    def save(self, *args, **kwargs):
        self.title_slug = slugify(self.title)
        super(BusinessUnit, self).save(*args, **kwargs)

    def show_sites(self):
        return ", ".join(self.seosite_set.all().values_list("domain",
                                                            flat=True))

    id = models.IntegerField('Business Unit Id', max_length=10,
                             primary_key=True)
    title = models.CharField(max_length=500, null=True, blank=True)
    title_slug = models.SlugField(max_length=500, null=True, blank=True)
    date_crawled = models.DateTimeField('Date Crawled')
    date_updated = models.DateTimeField('Date Updated')
    associated_jobs = models.IntegerField('Associated Jobs', default=0)
    customcareers = generic.GenericRelation(moc_models.CustomCareer)
    federal_contractor = models.BooleanField(default=False)
    ignore_includeinindex = models.BooleanField('Ignore "Include In Index"',
                                                default=False)

    # True if a BusinessUnit's descriptions are in markdown
    # Assumes that new business units will have support markdown
    enable_markdown = models.BooleanField('Enable Markdown for job '
                                          'descriptions', default=True)
    site_packages = models.ManyToManyField('postajob.SitePackage', null=True,
                                           blank=True)

    @staticmethod
    def clear_cache(buid):
        """Clears the cache for related sites."""
        sites = SeoSite.objects.filter(business_units=buid).exclude(
            site_tags__site_tag='network')
        SeoSite.clear_caches(sites)


class Country(models.Model):
    name = models.CharField(max_length=255, db_index=True)
    abbrev = models.CharField(max_length=255, blank=True, null=True,
                              db_index=True)
    abbrev_short = models.CharField(max_length=255, blank=True, null=True,
                                    db_index=True)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = 'Country'
        verbose_name_plural = 'Countries'


class State(models.Model):
    name = models.CharField(max_length=255, db_index=True)
    nation = models.ForeignKey(Country)

    def __unicode__(self):
        return self.name

    class Meta:
        unique_together = ('name', 'nation')
        verbose_name = 'State'
        verbose_name_plural = 'States'


class City(models.Model):
    name = models.CharField(max_length=255, db_index=True)
    nation = models.ForeignKey(Country)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = 'City'
        verbose_name_plural = 'Cities'


class CustomPage(FlatPage):
    group = models.ForeignKey(Group, blank=True, null=True)
    meta = models.TextField(blank=True)
    meta_description = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name = 'Custom Page'
        verbose_name_plural = 'Custom Pages'


class CompanyUser(models.Model):
    GROUP_NAME = 'Employer'
    ADMIN_GROUP_NAME = 'Partner Microsite Admin'

    user = models.ForeignKey(User)
    company = models.ForeignKey(Company)
    date_added = models.DateTimeField(auto_now=True)
    group = models.ManyToManyField('auth.Group', blank=True)

    def __unicode__(self):
        return 'Admin %s for %s' % (self.user.email, self.company.name)

    def save(self, *args, **kwargs):
        """
        Adds the user to the Employer group if it wasn't already a member.

        If the user is already a member of the Employer group, the Group app
        is smart enough to not add it a second time.
        """

        using = kwargs.get('using', 'default')

        inviting_user = kwargs.pop('inviting_user', None)
        group = Group.objects.using(using).get(name=self.GROUP_NAME)
        self.user.groups.add(group)

        # There are some cases where a CompanyUser may be adding themselves
        # and not being invited, so only create an invitation if we can
        # determine who is inviting them.
        if not self.pk and inviting_user:
            Invitation(invitee=self.user, inviting_company=self.company,
                       added_permission=group,
                       inviting_user=inviting_user).save(using=using)

        return super(CompanyUser, self).save(*args, **kwargs)

    class Meta:
        unique_together = ('user', 'company')
        db_table = 'mydashboard_companyuser'

    def make_purchased_microsite_admin(self):
        group, _ = Group.objects.get_or_create(name=self.ADMIN_GROUP_NAME)
        self.group.add(group)
        self.save()


@receiver(post_delete, sender=CompanyUser,
          dispatch_uid='post_delete_companyuser_signal')
def remove_user_from_group(sender, instance, **kwargs):
    # if a user is not associated with any more companies, we should remove
    # them from the employer group
    if not CompanyUser.objects.filter(user=instance.user):
        instance.user.groups.remove(Group.objects.get(name='Employer'))
        instance.user.save()
