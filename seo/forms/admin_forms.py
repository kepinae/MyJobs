import os
from fsm.widget import FSM
from taggit.forms import TagField, TagWidget

from django.conf import settings
from django import forms
from django.core import validators
from django.contrib import admin
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse_lazy
from django.core.validators import EMPTY_VALUES
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.csrf import csrf_protect

from postajob.models import SitePackage
from seo.models import (ATSSourceCode, BillboardImage,
                        BusinessUnit, Company, Configuration, CustomFacet,
                        CustomPage, GoogleAnalytics,
                        GoogleAnalyticsCampaign, SeoSite, SeoSiteFacet,
                        SiteTag, SpecialCommitment, ViewSource)

csrf_protect_m = method_decorator(csrf_protect)


class MyModelMultipleChoiceField(forms.ModelMultipleChoiceField):
    """
    Overrides the default ModelMultipleChoiceField.
    As far as I can tell, the only alteration is that clean() no longer runs 
    validation on value. -- Ashley 8/19/13

    """
    def __init__(self, queryset, cache_choices=False, required=True,
                 widget=None, label=None, initial=None,
                 help_text=None, *args, **kwargs):
        self.my_model = kwargs.pop('my_model', None)
        super(forms.ModelMultipleChoiceField, self)\
            .__init__(queryset, None, cache_choices, required, widget, label,
                      initial, help_text, *args, **kwargs)    

    def clean(self, value):
        if self.required and not value:
            raise ValidationError(self.error_messages['required'])
        elif not self.required and not value:
            return []
        if not isinstance(value, (list, tuple)):
            raise ValidationError(self.error_messages['list'])
        for pk in value:
            try:
                self.queryset.filter(pk=pk)
            except ValueError:
                raise ValidationError(self.error_messages['invalid_pk_value'] %
                                      pk)
        qs = self.my_model.objects.filter(pk__in=value)
        return qs
        

class MyModelChoiceField(forms.ModelChoiceField):
    """
    Overrides the default ModelChoiceField.
    As far as I can tell, the only alteration is that to_python() no longer 
    runs validation on primary key for value. -- Ashley 8/19/13
    """
    def __init__(self, queryset, empty_label=u"---------", cache_choices=False,
                 required=True, widget=None, label=None, initial=None,
                 help_text=None, to_field_name=None, *args, **kwargs):
        self.my_model = kwargs.pop('my_model', None)
        super(MyModelChoiceField, self)\
            .__init__(queryset, empty_label, cache_choices, required, widget,
                      label, initial, help_text, to_field_name, *args, **kwargs)

    def to_python(self, value):
        if value in EMPTY_VALUES:
            return None
        try:
            value = self.my_model.objects.get(id=value)
        except self.queryset.model.DoesNotExist:
            raise ValidationError(self.error_messages['invalid_choice'])
        return value


class RowPermissionsForm(forms.ModelForm):
    """
    Generic form used to filter selections on a ModelForms by the
    group of the user accessing the page.
    
    """
    group = MyModelChoiceField(Group.objects.order_by('name'), my_model=Group,
                               required=False)

    def __init__(self, data=None, user=None, *args, **kwargs):
        super(RowPermissionsForm, self).__init__(data, *args, **kwargs)
        field_querysets = {'group': {'qs': Group.objects.all(),
                                     'field_type': MyModelChoiceField,
                                     'widget': forms.widgets.Select()}}
        
        if user and not user.is_superuser:
            grps = [g.id for g in user.groups.all()]
            grp_qs = Group.objects.filter(id__in=grps)
            field_querysets['group']['qs'] = grp_qs

        for field, attrs in field_querysets.items():
            # This conditional is actually superfluous, but at the time of this
            # writing this feature branch was needed badly so we're holding off
            # on changing it now. Definitely needs to be removed in the future.
            if field not in self.fields:
                self.fields[field] = attrs['field_type'](queryset=attrs['qs'],
                                                         widget=attrs['widget'])
            else:
                # If the form already has the field, it will simply
                # set the querystring for the existing field to our dynamic
                # querystring. Otherwise every time it is initialized via
                # __init__ its queryset will be set back to
                # the full queryset, which is undesired behavior.
                self.fields[field].widget = attrs['widget']
                self.fields[field].queryset = attrs['qs']
                
        if user and not user.is_superuser and len(grp_qs) <= 1:
            self.fields['group'].empty_label = None


class SeoSiteReverseForm(forms.ModelForm):
    """
    This form is a template class used for models that need to provide mapping
    to an SeoSite object via a reverse many to many (meaning the association
    with the SeoSite model is done via a field on SeoSite, not on the model
    using this form). It instantiates a sites "field" for use in the admin,
    and handles the save functionality for it.

    WARNING: Ensure that sites are in your ModelAdmin fieldsets, or all
             relationships to SeoSite will be deleted on form save.
    
    Inputs:
    :forms.ModelForm:   Default django form object. Row permissions were
                        explicitley left out as the models that use this form
                        are intended for super user edits only.
    
    Returns:
    :model_object:      saved model object. Which model depends on how this form
                        is subclassed.
    """

    sites_widget = FSM('Site', reverse_lazy('site_admin_fsm'), lazy=True)
    sites = forms.ModelMultipleChoiceField(
        SeoSite.objects.order_by('domain'),
        required=False,
        widget=sites_widget
    )

    def __init__(self, *args, **kwargs):
        """
        Make sure we prepopulate the SeoSites that have already been selected.
        """
        super(SeoSiteReverseForm, self).__init__(*args, **kwargs)
        instance = kwargs.get('instance', None)

        if instance:
            self.fields['sites'].initial = {
                # Our FSM widget uses integer keys instead of strings
                site.id: 'selected' for site in instance.seosite_set.all()
            }

    def save(self, commit=True):
        added_sites = set()
        model_object = forms.ModelForm.save(self, commit)
        if model_object.__class__.__name__ == "BusinessUnit":
            model_object.save()
        for site in self.cleaned_data['sites']:
            added_sites.add(site)
        if model_object.pk:
            if set(added_sites) != set(model_object.seosite_set.all()):
                model_object.seosite_set = added_sites
        else:
            model_object.save()
            model_object.seosite_set = added_sites
        return model_object
        
        
class SeoSiteForm(RowPermissionsForm):
    configurations = MyModelMultipleChoiceField(
        Configuration.objects.all(),
        my_model=Configuration,
        required=False,
        widget=(admin.widgets.FilteredSelectMultiple('Configurations', False))
    )
    google_analytics = MyModelMultipleChoiceField(
        GoogleAnalytics.objects.all(),
        my_model=GoogleAnalytics,
        required=False,
        widget=(admin.widgets.FilteredSelectMultiple('Google Analytics', False))
    )
    billboard_images = MyModelMultipleChoiceField(
        BillboardImage.objects.all(),
        my_model=BillboardImage,
        required=False,
        widget=(admin.widgets.FilteredSelectMultiple('Billboard Images', False))
    )
    google_analytics_campaigns = MyModelChoiceField(
        GoogleAnalyticsCampaign.objects.all(),
        my_model=GoogleAnalyticsCampaign,
        required=False
    )
    business_units = MyModelMultipleChoiceField(
        BusinessUnit.objects.all(),
        my_model=BusinessUnit,
        required=False,
        widget=(admin.widgets.FilteredSelectMultiple('Business Units', False))
    )
    special_commitments = MyModelMultipleChoiceField(
        SpecialCommitment.objects.all(),
        my_model=SpecialCommitment,
        required=False,
        widget=(admin.widgets.FilteredSelectMultiple('Special Commitments',
                                                     False))
    )
    site_tags = MyModelMultipleChoiceField(
        SiteTag.objects.all(),
        my_model=SiteTag,
        required=False,
        widget=(admin.widgets.FilteredSelectMultiple('Site Tags', False))
    )
    ats_source_codes = MyModelMultipleChoiceField(
        ATSSourceCode.objects.all(),
        my_model=ATSSourceCode,
        required=False,
        widget=(admin.widgets.FilteredSelectMultiple('ATS Source Codes', False))
    )
    featured_companies = MyModelMultipleChoiceField(
        Company.objects.all(),
        my_model=Company,
        required=False,
        widget=(admin.widgets.FilteredSelectMultiple('Featured Companies',
                                                     False))
        )
    group = MyModelChoiceField(Group.objects.order_by('name'), my_model=Group,
                               required=False)
    domain = forms.CharField(max_length=255, label='Domain name',
                             validators=[])

    def __init__(self, data=None, user=None, *args, **kwargs):
        # The 'user' kwarg is passed in from the 'change_view' and 'add_view'
        # methods of the RowPermissionsAdmin class. That capability is the
        # main (only?) reason for creating a generic class in the first place.
        super(SeoSiteForm, self).__init__(data, user, *args, **kwargs)
        this = kwargs.get('instance')

        # Override some undesired default behavior
        if hasattr(self, 'errors') and 'domain' in self.errors:
            bad_error = 'Ensure this value has at most 100 characters'
            try:
                if self.errors['domain'][0].startswith(bad_error):
                    del self.errors['domain']
            except IndexError:
                pass

        if this:
            group = getattr(this, 'group') or Group()
        else:
            group = Group()
            
        models = {
            'configurations': Configuration,
            'google_analytics': GoogleAnalytics,
            'billboard_images': BillboardImage,
            'google_analytics_campaigns': GoogleAnalyticsCampaign,
            'business_units': BusinessUnit,
            'ats_source_codes': ATSSourceCode,
            'special_commitments': SpecialCommitment,
            'featured_companies': Company
        }
        field_querysets = {}

        # Build out a dictionary of fields that looks like:
        # {fieldname: {qs: queryset-to-use, field_type: forms.<FieldType>,
        #              widget: admin-widget-type}
        #
        # Then we'll use this to change self.fields.
        for field in models:
            inner = {}
            form_field = self.fields[field]

            # If we're changing an existing SeoSite model, filter by its group.
            # Otherwise, filter as normal based on superuser status.
            if field == 'special_commitments' or field == 'business_units' or\
            field == 'featured_companies':
                inner['qs'] = form_field.queryset
            elif this:
                inner['qs'] = form_field.queryset.filter(group=group)
            elif user.is_superuser:
                inner['qs'] = form_field.queryset
            else:
                inner['qs'] = form_field.queryset.filter(group__in=request.user\
                                                         .groups.all())
                
            inner['field_type'] = form_field
            inner['widget'] = form_field.widget
            field_querysets[field] = inner

        if not user.is_superuser:
            grps = [g.id for g in user.groups.all()]
            grp_qs = Group.objects.filter(id__in=grps)
            self.readonly_fields = ('domain', 'name')
    
        for field, attrs in field_querysets.items():
            self.fields[field].widget = attrs['widget']
            self.fields[field].queryset = attrs['qs']

        if not user.is_superuser and len(grp_qs) <= 1:
            self.fields['group'].empty_label = None

    
    def clean_configurations(self):
        data = self.cleaned_data['configurations']
        if data:
            if data.filter(status=1).count() > 1:
                raise ValidationError("Please select only one staging configura"
                                      "tion for this site.")
            if data.filter(status=2).count() > 1:
                raise ValidationError("Please select only one production "
                                      "configuration for this site.")
        return data

    class Meta:
        model = SeoSite


class SiteRowPermissionsForm(RowPermissionsForm):
    """
    Create a form such that SeoSite and Group fields are filtered according
    to user permissions. This is used by ModelForms that display an SeoSite
    multiselect box.

    """

    sites = MyModelMultipleChoiceField(
        SeoSite.objects.all(),
        my_model=SeoSite,
        required=False,
        widget=(admin.widgets.FilteredSelectMultiple('Sites', False))
    )

    def __init__(self, data=None, user=None, *args, **kwargs):
        super(SiteRowPermissionsForm, self).__init__(data, user, *args,
                                                     **kwargs)
        group = (getattr(kwargs.get('instance', self._meta.model()), 'group') or
                 Group())
        widget = admin.widgets.FilteredSelectMultiple('Sites', False)
        self.fields['sites'] = MyModelMultipleChoiceField(group.seosite_set.all(),
                                                          my_model=SeoSite,
                                                          required=False,
                                                          widget=widget)


class CustomFacetForm(SiteRowPermissionsForm):
    name = forms.CharField(label="Name", required=True,
                           help_text=("""A concise and descriptive
                                      name for this saved
                                      search, e.g.:
                                      us-nursing,
                                      texas-tech-support"""))
    title = forms.CharField(label="Title", required=False,
                            help_text=("""A comma-separated list of job titles
                                       to search on. Terms entered here will
                                       refer to job titles as provided in your
                                       company's job listings. e.g.:
                                       Dental Technician,Office Assistant
                                       """),
                            widget=forms.TextInput(attrs={'class': 'cf_field'}))
    keyword = TagField(label="Keywords", required=False,
                       widget=TagWidget(attrs={"class": "cf_field"}))
    city = forms.CharField(widget=forms.TextInput(attrs={"class": "cf_field"}),
                           required=False)
    state = forms.CharField(widget=forms.TextInput(attrs={"class": "cf_field"}),
                            required=False)

    text_input = forms.TextInput(attrs={"class": "cf_field"})
    country = forms.CharField(widget=text_input, required=False)
    company = forms.CharField(widget=text_input, required=False)
    onet = forms.CharField(widget=text_input, required=False,
                           help_text=("A comma-separated list of numeric onet "
                                      "codes."))
    querystring = forms.CharField(label="Raw Lucene Query", required=False,
                                  max_length=10000,
                                  widget=forms.Textarea(attrs={
                                      'size': '35',
                                      'cols': '50',
                                      'class': 'cf_field'}))
    search_preview = forms.CharField(label="Preview Search", required=False,
                                     widget=forms.Textarea(attrs={
                                         'size': '70',
                                         'cols': '100',
                                         'readonly': True}))
    group = MyModelChoiceField(Group.objects.order_by('name'), my_model=Group,
                               required=False)

    sites_widget = admin.widgets.FilteredSelectMultiple('Sites', False)
    sites = MyModelMultipleChoiceField(SeoSite.objects.all(), my_model=SeoSite,
                                       required=False, widget=sites_widget)

    business_units_widget = FSM('Business Unit', reverse_lazy('buid_admin_fsm'),
                                lazy=True, async=True)
    business_units = MyModelMultipleChoiceField(BusinessUnit.objects.all(),
                                                my_model=BusinessUnit,
                                                required=False,
                                                widget=business_units_widget)
    facet_type = forms.ChoiceField(required=False,
                                   choices=SeoSiteFacet.FACET_TYPE_CHOICES)
    facet_group = forms.ChoiceField(choices=SeoSiteFacet.FACET_GROUP_CHOICES)
    boolean_operation = forms.ChoiceField(required=False,
                                          choices=SeoSiteFacet.BOOLEAN_CHOICES)

    def clean_onet(self):
        data = self.cleaned_data['onet']
        if data:
            onets = data.split(',')
            for onet in onets:
                onet = onet.strip()
                if len(onet) > 10 or not onet.isdigit():
                    raise ValidationError("Please enter a valid onet code"
                                          " with only numeric values.")
        return data

    def save(self, commit=True):
        customfacet = super(CustomFacetForm, self).save(commit=commit)
        if not customfacet.pk:
            customfacet.save()

        sites = self.cleaned_data['sites']
        facet_type = self.cleaned_data['facet_type']
        boolean_operation = self.cleaned_data['boolean_operation']
        facet_group = self.cleaned_data['facet_group']
        for site in sites:
            try:
                facet, _ = SeoSiteFacet.objects.get_or_create(
                    seosite=site, customfacet=customfacet,
                    facet_type=facet_type, boolean_operation=boolean_operation,
                    facet_group=facet_group
                )
                facet.save()
            except SeoSiteFacet.MultipleObjectsReturned:
                pass

        #Adds keyword tags to customfacet. If tags don't get added here,
        #no keyword tags are passed to CustomFacet.save() for new
        #custom facets.
        keywords = self.cleaned_data['keyword']

        customfacet.keyword.add(*keywords)
        customfacet.save()
        return self.instance

        
    class Media:
        js = ("//d2e48ltfsb5exy.cloudfront.net/content_ms/files/ajax-solr/core/Core.js",
              "//d2e48ltfsb5exy.cloudfront.net/content_ms/files/ajax-solr/core/AbstractManager.js",
              "//d2e48ltfsb5exy.cloudfront.net/content_ms/files/ajax-solr/core/Parameter.js",
              "//d2e48ltfsb5exy.cloudfront.net/content_ms/files/ajax-solr/core/ParameterStore.js",
              "//d2e48ltfsb5exy.cloudfront.net/content_ms/files/ajax-solr/core/ParameterStore.js",
              "//d2e48ltfsb5exy.cloudfront.net/content_ms/files/ajax-solr/core/AbstractWidget.js",
              "//d2e48ltfsb5exy.cloudfront.net/content_ms/files/ajax-solr/Widgets.js",
              "//d2e48ltfsb5exy.cloudfront.net/content_ms/files/ajax-solr/managers/Manager.jquery.js",
              "//d2e48ltfsb5exy.cloudfront.net/content_ms/files/facet_builder2.154-17.js")
                    
    class Meta:
        model = CustomFacet
        exclude = ("name_slug", "url_slab")


class CustomPageForm(SiteRowPermissionsForm):
    def __init__(self, data=None, user=None, *args, **kwargs):
        super(CustomPageForm, self).__init__(data, user, *args, **kwargs)
        templates = filter(lambda x: x.endswith('.html'), 
                           os.listdir('%s/templates/flatpages' % settings.PROJECT_PATH))
        template_choices = (("flatpages/%s" % temp, temp) for temp in templates)
        self.fields['template_name'].widget = forms.widgets.Select(
            choices = template_choices)
        self.fields['template_name'].help_text = None
        self.fields['content'].widget.attrs.update({
            'style': 'width: 80%; height: 440px'})
        
    url = forms.RegexField(label=_("URL"), max_length=100, regex=r'^[-\w/\.~]+$',
        help_text = _("Example: '/about/contact/'. Make sure to have leading"
                      " and trailing slashes."),
        error_message = _("This value must contain only letters, numbers,"
                          " dots, underscores, dashes, slashes or tildes."))

    class Meta:
        model = CustomPage
        

class BillboardImageForm(SiteRowPermissionsForm):
    def __init__(self, data=None, user=None, *args, **kwargs):
        super(BillboardImageForm, self).__init__(data, user, *args, **kwargs)
        if kwargs.has_key('instance'):
            if kwargs['instance'].group:
                site_vals = kwargs['instance'].group.seosite_set.all()
            else:
                site_vals = SeoSite.objects.none()
            initial_vals = [s.pk for s in kwargs['instance'].seosite_set.all()]
        else:
            site_vals = SeoSite.objects.none()
            initial_vals = []
        self.fields['sites'] = MyModelMultipleChoiceField(
                                   site_vals, 
                                   my_model=SeoSite,
                                   required=False, 
                                   initial=initial_vals,
                                   widget=(admin.widgets\
                                                .FilteredSelectMultiple('Sites',
                                                                        False)))

    def save(self, commit=True):
        added_sites = set()
        bi = super(BillboardImageForm, self).save(commit)

        for site in self.cleaned_data['sites']:
            added_sites.add(site)
        if bi.pk:
            if added_sites != set(bi.seosite_set.all()):
                bi.seosite_set = added_sites
        else:
            bi.save()
            bi.seosite_set = added_sites
            
        return bi

    class Meta:
        model = BillboardImage


class ConfigurationForm(RowPermissionsForm):
    sites = MyModelMultipleChoiceField(
        SeoSite.objects.all(),
        my_model=SeoSite,
        required=False,
        widget=(admin.widgets.FilteredSelectMultiple('Sites', False))
    )
    group = MyModelChoiceField(Group.objects.order_by('name'), my_model=Group,
                               required=False)

    def __init__(self, data=None, user=None, *args, **kwargs):
        super(ConfigurationForm, self).__init__(data, user, *args, **kwargs)
        templates = filter(lambda x: x.endswith('.html'),
                           os.listdir('%s/templates/home_page' %
                                      settings.PROJECT_PATH))
        template_choices = (("home_page/%s" % temp, temp) for temp in templates)

        this = kwargs.get('instance')

        if this:
            self.grp = getattr(this, 'group') or Group()
        else:
            self.grp = Group()

        self.fields['home_page_template'].widget = forms.widgets.Select(
            choices=template_choices)
        self.fields['meta'].widget.attrs['rows'] = '30'
        # widen text areas
        for field in ['defaultBlurb', 'meta', 'wide_header', 'header', 'body',
                      'footer', 'wide_footer']:
            self.fields[field].widget.attrs.update({
                'style': 'width: 80%; height: 440px;'})

    def save(self, commit=True):
        # Associate the SeoSite selection from the UI with the Configuration
        # specified by this form. We've got to first save the form with
        # commit=False, then populate the seo_seosite_configuration through-
        # table in the database. This is accomplished because the '=' operator
        # is overloaded in the ORM when it comes to ManyToMany fields. By using
        # the '=', it's calling 'form.save_m2m()' behind the scenes.
        # This is required because the Configuration model doesn't have sites or
        # group attributes (that is, the seo_configuration table doesn't have
        # columns for that data). 
        configuration = super(ConfigurationForm, self).save(commit=commit)
        sites = self.cleaned_data['sites']
        group = self.cleaned_data['group']
        
        if not configuration.pk:
            configuration.save()

        configuration.seosite_set = [s for s in sites if s.group == group]
        return self.instance
        
    class Meta:
        model = Configuration
        widgets = {
            'backgroundColor': forms.TextInput(attrs={
                'name': 'backgroundColor_',
                'class': "color {pickerFaceColor:'#CCC', caps:false}"}),
            'fontColor': forms.TextInput(attrs={
                'name': 'fontColor_',
                'class': "color {pickerFaceColor:'#CCC', caps:false}"}),
            'primaryColor': forms.TextInput(attrs={
                'name': 'primaryColor_',
                'class': "color {pickerFaceColor:'#CCC', caps:false}"}),
        }
        exclude = [
            'location_tag',
            'title_tag',
            'facet_tag',
            'moc_tag',
            'company_tag',
            'directemployers_link',
            'revision'
        ]


class BusinessUnitForm(SeoSiteReverseForm):    
    class Meta:
        model = BusinessUnit

    def __init__(self, *args, **kwargs):
        super(BusinessUnitForm, self).__init__(*args, **kwargs)

        sites = SeoSite.objects.all()
        site_package_label = 'Show on these sites only'
        site_packages_widget = FSM(site_package_label,
                                   reverse_lazy('site_fsm'), async=True)
        self.fields['site_packages'] = forms.ModelMultipleChoiceField(
            queryset=sites, help_text='', label=site_package_label,
            required=False, widget=site_packages_widget)

        if self.instance.pk and self.instance.site_packages:
            # Since we're not using actual site_packages for the site_packages,
            # the initial data also needs to be manually set.
            query = {'site_package__in': self.instance.site_packages.all()}
            initial = [site.pk for site in SeoSite.objects.filter(**query)]
            self.initial['site_packages'] = {site: 'selected'
                                             for site in initial}

        # Override the default help_text since for some reason
        # ModelMultipleChoiceFields ignore the help_text kwarg.
        self.fields['site_packages'].help_text = 'This is set on ' \
                                                 'import and will take until ' \
                                                 'the next import to show ' \
                                                 'up or stop.'

    def clean_site_packages(self):
        """
        Convert from SeoSite or network sites to a SitePackage.

        """
        sites = self.cleaned_data.get('site_packages')
        site_packages = []
        for site in sites:
            if not hasattr(site, 'site_package') or not site.site_package:
                # If a site doesn't already have a site_package specific
                # to it create one.
                package = SitePackage(name=site.domain)
                package.make_unique_for_site(site)
            site_packages.append(site.site_package)

        return site_packages

    def save(self, commit=True):
        sites = self.cleaned_data['site_packages']
        bu = super(BusinessUnitForm, self).save(commit)

        # The pk must exist before the manytomany relationship can be created.
        if not hasattr(bu, 'pk') or not bu.pk:
            bu.save()

        [bu.site_packages.add(s) for s in sites]

        return bu

        
class CompanyForm(SeoSiteReverseForm):    
    job_source_ids_widget = FSM('Job Sources', reverse_lazy('buid_admin_fsm'),
                                lazy=True)
    job_source_ids = MyModelMultipleChoiceField(BusinessUnit.objects.all(),
                                                my_model=BusinessUnit,
                                                required=False,
                                                widget=job_source_ids_widget)
    class Meta:
        model = Company
        
        
class SpecialCommitmentForm(SeoSiteReverseForm):        
    class Meta:
        model = SpecialCommitment


class SiteTagForm(forms.ModelForm):
    class Meta:
        model = SiteTag


class GoogleAnalyticsCampaignForm(SeoSiteReverseForm):        
    class Meta:
        model = GoogleAnalyticsCampaign


class ATSSourceCodeForm(SeoSiteReverseForm):        
    class Meta:
        model = ATSSourceCode


class ViewSourceForm(SeoSiteReverseForm):        
    class Meta:
        model = ViewSource


class UploadJobFileForm(forms.Form):
    job_file = forms.FileField(label='Job File')
