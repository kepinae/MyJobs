from django import forms
from django.contrib import admin
from django.contrib.admin import helpers
from django.contrib.admin.util import unquote
from django.contrib.admin.sites import NotRegistered
from django.contrib.admin.views.main import ChangeList
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from django.contrib.sites.models import Site
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.core.cache import cache
from django.db import models, transaction
from django.forms.formsets import all_valid
from django.http import Http404
from django.utils.encoding import force_unicode
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

import djcelery.admin
from celery import current_app
from djcelery.admin_utils import action

import tasks
from seo.forms.admin_forms import (ConfigurationForm, CustomFacetForm,
                                   CustomPageForm, RowPermissionsForm,
                                   BillboardImageForm, MyModelChoiceField,
                                   MyModelMultipleChoiceField, SeoSiteForm,
                                   BusinessUnitForm,
                                   GoogleAnalyticsCampaignForm,
                                   SpecialCommitmentForm, CompanyForm,
                                   ATSSourceCodeForm, ViewSourceForm,
                                   SiteTagForm)
from seo.models import (ATSSourceCode, BillboardHotspot, BillboardImage,
                        BusinessUnit, Company, Configuration, CustomFacet,
                        CustomPage, FlatPage, GoogleAnalytics,
                        GoogleAnalyticsCampaign, SeoSite, SeoSiteFacet,
                        SeoSiteRedirect, SiteTag, SpecialCommitment, ViewSource)
from seo.queryset_copier import copy_following_relationships
from seo.signals import check_message_queue


csrf_protect_m = method_decorator(csrf_protect)


class GroupListFilter(admin.SimpleListFilter):
    """
    Limits group filter selection and results to only groups the user is a
    member of unless the user is a superadmin.
    """
    
    title = _('Group')
    parameter_name = 'filtered_groups'
    
    def lookups(self, request, model_admin):
        """
        Limits filter selection.
        """
        
        if request.user.is_superuser:
            return [(group.name, group.name) for group in Group.objects.all()]
        return [(group.name, group.name) for group in request.user.groups.all()]

    def queryset(self, request, queryset):
        """
        Limits query results.
        """
        
        if not self.value():
            return queryset
        return queryset.filter(group__name=self.value())


class SeoCeleryTaskAdmin(djcelery.admin.TaskMonitor):
    djcelery.admin.TaskMonitor.actions.append('resend_task')

    @action(_("Resend Task"))
    def resend_task(self, request, queryset):
        """
        Resend tasks in queryset. Only works for tasks whose arguments
        can be completely represented by strings in task state.

        """
        #Using python's ast.literal_eval to evaluate string representations
        #of args and kwargs as a tuple and dictionary
        import ast
        with current_app.default_connection() as connection:
            for state in queryset:
                if "update_solr" in state.name:
                    args = ast.literal_eval(state.args)
                    kwargs = ast.literal_eval(state.kwargs)
                    tasks.task_update_solr.delay(*args, **kwargs)
                else:
                    messages.info(request,
                                  u"Resend not supported for that task type")

admin.site.unregister(djcelery.models.TaskState)
admin.site.register(djcelery.models.TaskState, SeoCeleryTaskAdmin)


class ConfigurationAdmin (admin.ModelAdmin):
    form = ConfigurationForm
    list_display = ('__unicode__', 'show_sites', 'group', 'status_title')
    list_filter = [GroupListFilter]
    save_on_top = True
    search_fields = ['seosite__domain', 'seosite__name', 'title']

    # Disable bulk delete on this model to prevent accidental catastrophe
    def get_actions(self, request):
        actions = super(ConfigurationAdmin, self).get_actions(request)
        if request.user:
            del actions['delete_selected']
        return actions

    actions = ['clone_objects', ]
    
    def queryset(self, request):
        qs = super(ConfigurationAdmin, self).queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(group__in=request.user.groups.all())
        
    def clone_objects(self, request, queryset):
        def clone(from_object):
            args = dict([(fld.name, getattr(from_object, fld.name))
                    for fld in from_object._meta.fields
                            if fld is not from_object._meta.pk]);
            args['title'] = args['title'] + " (copy)"
            args['status'] = 3

            return from_object.__class__.objects.create(**args)

        if not hasattr(queryset, '__iter__'):
            queryset = [queryset]

        # We always have the objects in a list now
        objs = []
        for obj in queryset:
            obj = clone(obj)
            obj.save()
            objs.append(obj)
    clone_objects.short_description = "Copy the selected configurations"
        
    def get_form(self, request, obj=None, **kwargs):
        this = super(ConfigurationAdmin, self).get_form(request, obj, **kwargs)
        my_group_fieldset = [('title', 'group', 'status', 'percent_featured'),
                             ('view_all_jobs_detail', 'show_social_footer',
                              'show_saved_search_widget'),
                             'sites', ]
        my_fieldsets = [
            ('Basic Info', {'fields': [
                ('title', 'view_all_jobs_detail', 'status',
                 'percent_featured'),
                ('view_all_jobs_detail', 'show_social_footer',
                 'show_saved_search_widget', ),
                'sites']}),
            ('Home Page Options', {'fields': [
                ('home_page_template', 'publisher',
                 'show_home_social_footer',
                 'show_home_microsite_carousel')]}),
            ('Search Box Options', {'fields': [
                ('where_label', 'where_placeholder', 'where_helptext'),
                ('what_label', 'what_placeholder', 'what_helptext'),
                ('moc_label', 'moc_placeholder', 'moc_helptext')
            ]}),
            ('Blurb Options', {'fields': ['defaultBlurbTitle',
                                          'defaultBlurb']}),
            ('Navigation Options', {'fields': [
                ('browse_country_order', 'browse_country_text',
                 'browse_country_show'),
                ('browse_state_order', 'browse_state_text',
                 'browse_state_show'),
                ('browse_city_order', 'browse_city_text', 'browse_city_show'),
                ('browse_title_order', 'browse_title_text',
                 'browse_title_show'),
                ('browse_facet_order', 'browse_facet_text',
                 'browse_facet_show'),
                ('browse_facet_order_2', 'browse_facet_text_2',
                 'browse_facet_show_2'),
                ('browse_facet_order_3', 'browse_facet_text_3',
                 'browse_facet_show_3'),
                ('browse_company_order', 'browse_company_text',
                 'browse_company_show'),
                ('browse_moc_order', 'browse_moc_text', 'browse_moc_show'),
                ('num_subnav_items_to_show', 'num_filter_items_to_show',
                 'num_job_items_to_show')]}),
            ('Stylesheet', {'fields': [('backgroundColor', 'fontColor',
                                        'primaryColor'),
                                       ]}),
            ('Template Includes', {'fields': ['meta', 'wide_header', 'header',
                                              'body', 'footer', 'wide_footer']}),
        ]
        this.base_fields['group'].queryset = Group.objects.all()
        this.base_fields['group'].required = False
        this.base_fields['sites'].queryset = SeoSite.objects.all()
        self.fieldsets = my_fieldsets
        if obj:
            this.base_fields['sites'].queryset = (SeoSite.objects
                                                  .filter(group=obj.group))
            this.base_fields['sites'].initial = [o.pk for o in obj.seosite_set
                                                 .filter(group=obj.group)]

            if request.user.is_superuser or request.user.groups.count() >= 1:
                if not request.user.is_superuser:
                    this.base_fields['group'].queryset = Group.objects.filter(
                        id__in=request.user.groups.all())
                self.fieldsets[0][1]['fields'] = my_group_fieldset
                this.base_fields['group'].required = True
        else:
            this.base_fields['sites'].initial = []
            this.base_fields['sites'].queryset = SeoSite.objects.filter(id=None)
            if request.user.is_superuser or request.user.groups.count() >= 1:
                self.fieldsets[0][1]['fields'] = my_group_fieldset
                this.base_fields['group'].required = True
                if not request.user.is_superuser:
                    this.base_fields['group'].queryset = Group.objects.filter(
                        id__in=request.user.groups.all())
        return this

    @check_message_queue        
    def delete_model(self, request, *args, **kwargs):
        super(ConfigurationAdmin, self).delete_model(request, *args, **kwargs)

    @check_message_queue        
    def save_model(self, request, obj, form, change):
        if obj.status == [1, 2]:
            #Force an evaluation of obj site keys. When obj.seosite_set was used
            #in queries for qs, an error would be thrown if the two objects had
            #been queried from different databases
            obj_site_keys = [site.pk for site in obj.seosite_set.all()]
            qs = Configuration.objects.filter(seosite__pk__in=obj_site_keys,
                                              status=obj.status)
            if obj.pk:
                qs = qs.exclude(pk=obj.pk)
            if qs.exists():
                qs[0].seosite_set = (set(qs[0].seosite_set.all()) -
                                     set(obj.seosite_set.all()))
        if (not request.user.is_superuser and
            request.user.groups.count() is 1 and
            not obj.group):
            obj.group = request.user.groups.all()[0]
        obj.save()

      
class BusinessUnitAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'show_sites', 'associated_jobs',
                    'date_crawled', 'date_updated')
    actions = ['reset_jobs', 'force_create', 'clear']
    readonly_fields = ('associated_jobs',)
    form = BusinessUnitForm
    search_fields = ['seosite__domain', 'seosite__name', 'title', 'id']
    prepopulated_fields = {'title_slug': ('title',)}
    fieldsets = [
        ('Basics', {'fields': [('id', 'title', 'title_slug',
                                'associated_jobs', 'federal_contractor',
                                'enable_markdown', 'ignore_includeinindex'),
                               ('date_crawled', 'date_updated')]}),
        ('Sites', {'fields': ['sites']}),
        ('Imports', {'fields': ['site_packages']}),
    ]
    change_form_template = "admin/seo/businessunit/change_form.html"

    def reset_jobs(self, request, queryset):
        """
        Sends a message via Celery to download & parse the feedfile for a
        given Business Unit, then write the results to the Solr index and
        the RDBMS.

        """
        for business_unit in queryset:
            tasks.task_update_solr.delay(business_unit.id, force=True)
            
        messages.info(request, u"{alljobs} {busiunitid} {reprocess}".format(
            alljobs=_("All jobs for Business Unit:"),
            busiunitid=(business_unit.id),
            reprocess=_("will be re-processed shortly."))
        )
    reset_jobs.short_description = _("Refresh all jobs in business unit")
    
    def clear(self, request, queryset):
        for jsid in queryset:
            tasks.task_clear.delay(jsid)
            tasks.task_clear_solr.delay(jsid.id)
            
        messages.info(request, u"{alljobs} {jsident} {remove}".format(
            alljobs=_("All jobs for Business Unit:"),
            jsident=(jsid.id),
            remove=_("will be removed shortly."))
        )
    clear.short_description = _("Clear jobs from business unit")

    def force_create(self, request, queryset):
        for jsid in queryset:
            tasks.task_force_create.delay(jsid)

        messages.info(request, u"{feedfile} {jsident} {writtenout}".format(
            feedfile=_("A new feed file for Business Unit:"),
            jsident=(jsid.id),
            writtenout=_("will be written out and parsed shortly."))
        )
    force_create.short_description = _("Force creation of business unit feed")

    
class MyUserAdmin(UserAdmin):
    filter_horizontal = ('user_permissions', 'groups')

        
class GoogleAnalyticsForm(forms.ModelForm):
    sites = MyModelMultipleChoiceField(SeoSite.objects.all(), my_model=SeoSite,
                                       required=False,
                                       widget=(admin.widgets\
                                               .FilteredSelectMultiple('Sites',
                                                                       False)))
    group = MyModelChoiceField(Group.objects.order_by('name'), my_model=Group,
                               required=False)
          
    def save(self, commit=True):
        added_sites = set()
        ga = forms.ModelForm.save(self, commit)
        for site in self.cleaned_data['sites']:
            added_sites.add(site)
        if ga.pk:
            if set(added_sites) != set(ga.seosite_set.all()):
                ga.seosite_set = added_sites
        else:
            ga.save()
            ga.seosite_set = added_sites
        return ga

    class Meta:
        model = GoogleAnalytics

        
class GoogleAnalyticsAdmin(admin.ModelAdmin):
    
    form = GoogleAnalyticsForm    
    list_display = ('web_property_id', 'group', 'show_sites')
    search_fields = ['seosite__domain', 'seosite__name', 'web_property_id']
    
    def queryset(self, request):
        qs = super(GoogleAnalyticsAdmin, self).queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(group__in=request.user.groups.all())
        
    def get_form(self, request, obj=None, **kwargs):
        this = super(GoogleAnalyticsAdmin, self).get_form(request, obj,
                                                          **kwargs)
        my_group_fieldset = ['group', 'sites']
        my_fieldsets = [
            ('Sites', {'fields': ['sites']}),
            ('Anlytics ID', {'fields': ['web_property_id']}),
        ]
        this.base_fields['group'].queryset = Group.objects.all()
        this.base_fields['group'].required = False
        this.base_fields['sites'].queryset = SeoSite.objects.all()
        self.fieldsets = my_fieldsets
        if obj:
            this.base_fields['sites'].queryset = SeoSite.objects.filter(
                group=obj.group)
            this.base_fields['sites'].initial = [o.pk for o in obj.seosite_set\
                                                  .filter(group=obj.group)]
            if request.user.is_superuser or request.user.groups.count() > 1:
                if not request.user.is_superuser:
                    this.base_fields['group'].queryset = Group.objects.filter(
                        id__in=request.user.groups.all())
                self.fieldsets[0][1]['fields'] = my_group_fieldset
                this.base_fields['group'].required = True
        else:
            this.base_fields['sites'].initial = []
            this.base_fields['sites'].queryset = SeoSite.objects.filter(id=None)
            if request.user.is_superuser or request.user.groups.count() > 1:
                self.fieldsets[0][1]['fields'] = my_group_fieldset
                this.base_fields['group'].required = True
                if not request.user.is_superuser:
                    this.base_fields['group'].queryset = Group.objects.filter(
                        id__in=request.user.groups.all())
        return this
        
    def save_model(self, request, obj, form, change):
        if (not request.user.is_superuser and
            request.user.groups.count() is 1 and
            not obj.group):
            obj.group = request.user.groups.all()[0]
        obj.save()


class RowPermissionsAdmin(admin.ModelAdmin):
    """
    A generic ModelAdmin form for models that need so-called row-level
    permisions on their admin pages. The impetus for creating this is
    mostly due to the fact that by default, the request.user is not
    passed to the form. By overriding the add_view and change_view
    methods, we can then pass that data to our RowPermissionForm, and use
    it to filter results as appropriate.
    
    """
    form = RowPermissionsForm
    
    def queryset(self, request):
        qs = super(RowPermissionsAdmin, self).queryset(request)

        if request.user.is_superuser:
            return qs
        else:
            return qs.filter(group__in=request.user.groups.all())

    def get_form(self, request, obj=None, **kwargs):
        return self.form

    @csrf_protect_m
    @transaction.commit_on_success
    def add_view(self, request, form_url='', extra_context=None):
        """The 'add' admin view for this model."""
        model = self.model
        opts = model._meta

        if not self.has_add_permission(request):
            raise PermissionDenied

        form = self.form(user=request.user)
        if request.method == 'POST':
            form = self.form(data=request.POST, user=request.user)
            if form.is_valid():
                new_object = self.save_form(request, form, change=False)
                form.save()
                self.log_addition(request, new_object)
                return self.response_add(request, new_object)
            else:
                new_object = form
        else:
            # Prepare the dict of initial data from the request.
            # We have to special-case M2Ms as a list of comma-separated PKs.
            initial = dict(request.GET.items())
            for k in initial:
                try:
                    f = opts.get_field(k)
                except models.FieldDoesNotExist:
                    continue
                if isinstance(f, models.ManyToManyField):
                    initial[k] = initial[k].split(",")

        adminForm = helpers.AdminForm(form, list(self.get_fieldsets(request)),
                                      self.prepopulated_fields,
                                      self.get_readonly_fields(request),
                                      model_admin=self)
        media = self.media + adminForm.media
        context = {
            'title': _('Add ') + force_unicode(opts.verbose_name),
            'adminform': adminForm,
            'is_popup': request.REQUEST.has_key('_popup'),
            'show_delete': False,
            'media': mark_safe(media),
            'inline_admin_formsets': [],
            'errors': helpers.AdminErrorList(form, []),
            'app_label': opts.app_label,
        }
        context.update(extra_context or {})
        return self.render_change_form(request, context, form_url=form_url,
                                       add=True)
        
    @csrf_protect_m
    @transaction.commit_on_success
    def change_view(self, request, object_id, extra_context=None):
        """The 'change' admin view for this model."""
        model = self.model
        opts = model._meta
        obj = self.get_object(request, unquote(object_id))
        if not self.has_change_permission(request, obj):
            raise PermissionDenied

        if obj is None:
            raise Http404(u"{name}{transblock}{key} {noexist}".format(
                name=force_unicode(opts.verbose_name),
                transblock=_("object with primary key"),
                key=escape(object_id),
                noexist=_(" does not exist.")
            ))

        if request.method == 'POST' and request.POST.has_key("_saveasnew"):
            return self.add_view(request, form_url='../add/')

        form = self.form(user=request.user, instance=obj)
        if request.method == 'POST':
            form = self.form(data=request.POST, user=request.user,
                             instance=obj)
            if form.is_valid():
                form_validated = True
                # Store the saved but uncommitted form
                new_object = self.save_form(request, form, change=True)
            else:
                form_validated = False
                new_object = obj

            if form_validated:
                form.save()
                change_message = self.construct_change_message(request, form, [])
                self.log_change(request, new_object, change_message)
                return self.response_change(request, new_object)

        adminForm = helpers.AdminForm(form, self.get_fieldsets(request, obj),
                                      self.prepopulated_fields,
                                      self.get_readonly_fields(request, obj),
                                      model_admin=self)
        media = self.media + adminForm.media

        context = {
            'title': _('Change ') + force_unicode(opts.verbose_name),
            'adminform': adminForm,
            'object_id': object_id,
            'original': obj,
            'is_popup': request.REQUEST.has_key('_popup'),
            'media': mark_safe(media),
            'inline_admin_formsets': [],
            'errors': helpers.AdminErrorList(form, []),
            'app_label': opts.app_label,
        }
        context.update(extra_context or {})
        return self.render_change_form(request, context, change=True, obj=obj)

    def save_model(self, request, obj, form, change):
        if (not request.user.is_superuser and
            request.user.groups.count() is 1 and
            not obj.group):
            obj.group = request.user.groups.all()[0]
        obj.save()         


class CustomFacetAdmin(RowPermissionsAdmin):
    form = CustomFacetForm
    search_fields = ['country', 'state', 'city', 'title', 'name']
    list_display = ('name', 'last_updated', 'group')
    list_filter = (GroupListFilter,)
    fieldsets = (
        (None, {'fields': [('name', 'group'), ('always_show',
                                               'show_production')]}),
        ('Search terms', {'fields': ['title', 'keyword', 'company', 'onet',
                                     ('country', 'state', 'city'),
                                     'business_units']}),
        ('Advanced options', {'classes': ('collapse',),
                              'fields': [('querystring', 'search_preview'),
                                         'show_blurb', 'blurb']}),
        ('Add Seo Site Facets', {'classes': ('collapse', ),
                                 'fields': ['facet_group',
                                            'sites', 'facet_type',
                                            'boolean_operation']})
        )
    save_as = True

    def results(self, obj):
        cache_key = 'savedsearch_count:%s' % obj.id
        results_count = cache.get(cache_key)
        if not results_count:
            results_count = obj.get_sqs().count()
            cache.set(cache_key, results_count, 600)
        return results_count
    results.short_description = 'Results Count'
        
    def last_updated(self, obj):
        return str(obj.date_created)
    last_updated.short_description = 'Last Updated'


class CustomPageAdmin(RowPermissionsAdmin):
    form = CustomPageForm
    filter_horizontal = ('sites',)
    list_display = ('url', 'title', 'group')
    fieldsets = (
        (None, {'fields': [('url', 'group'), ('title', 'meta_description'),
                           'content', 'sites']}),
        ('Advanced options', {'classes': ('collapse',),
                              'fields': ('enable_comments',
                                         'registration_required',
                                         'template_name', 'meta')}),
    ) 
    list_filter = (GroupListFilter, 'enable_comments', 'registration_required')
    search_fields = ('url', 'title')

    
class BillboardHotspotInline(admin.StackedInline):
    model = BillboardHotspot
    extra = 0
    can_delete = True 
    fieldsets = (
        (None, {'fields': [('title', 'url', 'display_url'), 'text']}),
        (None, {'fields': [('offset_x', 'offset_y')]}),
        (None, {'fields': [('primary_color', 'font_color',
                            'border_color')]}),
    )

    def formfield_for_dbfield(self, db_field, **kwargs):
        attrs = {}

        if db_field.attname == 'text':
            kwargs['widget'] = forms.Textarea(attrs=attrs)
        else:
            if db_field.attname == 'primary_color':
                attrs = {'name': 'primaryColor_',
                         'size': 15,
                         'class': "color {pickerFaceColor:'#CCC', caps:false}"}
            elif db_field.attname == 'font_color':
                attrs = {'name': 'fontColor_',
                         'size': 15,
                         'class': "color {pickerFaceColor:'#CCC', caps:false}"}
            elif db_field.attname == 'border_color':
                attrs = {'name': 'borderColor_',
                         'size': 15,
                         'class': "color {pickerFaceColor:'#CCC', caps:false}"}
            kwargs['widget'] = forms.TextInput(attrs=attrs)
        return super(BillboardHotspotInline, self).formfield_for_dbfield(
            db_field, **kwargs)


class BillboardImageAdmin(RowPermissionsAdmin):
    form = BillboardImageForm
    save_on_top = True
    search_fields = ('title', 'seosite__domain', 'seosite__name')
    list_display = ('title', 'group', 'on_sites', 'has_hotspots',
                    'number_of_hotspots')
    # in order to get the below to work, we will need to write a custom
    # filterspec. At the time of this comment, the benefit doesn't warrent the
    # extra work. Jason Sole 10/17/12
    #
    # list_filter = ['has_hotspots']
    #
    inlines = [BillboardHotspotInline,]

    fieldsets = (
        ('General', {'fields': [('title', 'group')]}),
        ('Image Info', {'fields': [('image_url', 'source_url',
                                    'copyright_info')]}),
        ('Logo Info',  {'fields': [('logo_url', 'sponsor_url')]}),
        ('Sites', {'fields': ['sites']}),
    )

    @csrf_protect_m
    @transaction.commit_on_success
    def add_view(self, request, form_url='', extra_context=None):
        """The 'add' admin view for this model."""
        model = self.model
        opts = model._meta

        if not self.has_add_permission(request):
            raise PermissionDenied

        ModelForm = self.get_form(request)
        formsets = []
        if request.method == 'POST':
            form = ModelForm(request.POST, request.user)
            if form.is_valid():
                new_object = self.save_form(request, form, change=False)
                form_validated = True
            else:
                form_validated = False
                new_object = self.model()
            prefixes = {}
            self.inline_instances = check_inline_instance(self, request)
            for FormSet, inline in zip(self.get_formsets(request), self.inline_instances):
                prefix = FormSet.get_default_prefix()
                prefixes[prefix] = prefixes.get(prefix, 0) + 1
                if prefixes[prefix] != 1:
                    prefix = "%s-%s" % (prefix, prefixes[prefix])
                formset = FormSet(data=request.POST, files=request.FILES,
                                  instance=new_object,
                                  save_as_new="_saveasnew" in request.POST,
                                  prefix=prefix, queryset=inline.queryset(request))
                formsets.append(formset)
            if all_valid(formsets) and form_validated:
                self.save_model(request, new_object, form, change=False)
                form.save_m2m()
                for formset in formsets:
                    self.save_formset(request, form, formset, change=False)

                self.log_addition(request, new_object)
                return self.response_add(request, new_object)
        else:
            # Prepare the dict of initial data from the request.
            # We have to special-case M2Ms as a list of comma-separated PKs.
            initial = dict(request.GET.items())
            for k in initial:
                try:
                    f = opts.get_field(k)
                except models.FieldDoesNotExist:
                    continue
                if isinstance(f, models.ManyToManyField):
                    initial[k] = initial[k].split(",")
            form = self.form(user=request.user, initial=initial)
            prefixes = {}
            self.inline_instances = check_inline_instance(self, request)
            for FormSet, inline in zip(self.get_formsets(request),
                                       self.inline_instances):
                prefix = FormSet.get_default_prefix()
                prefixes[prefix] = prefixes.get(prefix, 0) + 1
                if prefixes[prefix] != 1:
                    prefix = "%s-%s" % (prefix, prefixes[prefix])
                formset = FormSet(instance=self.model(), prefix=prefix,
                                  queryset=inline.queryset(request))
                formsets.append(formset)

        adminForm = helpers.AdminForm(form, list(self.get_fieldsets(request)),
            self.prepopulated_fields, self.get_readonly_fields(request),
            model_admin=self)
        media = self.media + adminForm.media

        inline_admin_formsets = []
        self.inline_instances = check_inline_instance(self, request)
        for inline, formset in zip(self.inline_instances, formsets):
            fieldsets = list(inline.get_fieldsets(request))
            prepopulated_fields = inline.get_prepopulated_fields(request)
            readonly = list(inline.get_readonly_fields(request))
            inline_admin_formset = helpers.InlineAdminFormSet(inline, formset,
                fieldsets, prepopulated_fields, readonly, model_admin=self)
            inline_admin_formsets.append(inline_admin_formset)
            media = media + inline_admin_formset.media

        context = {
            'title': _('Add ') + force_unicode(opts.verbose_name),
            'adminform': adminForm,
            'is_popup': "_popup" in request.REQUEST,
            'show_delete': False,
            'media': mark_safe(media),
            'inline_admin_formsets': inline_admin_formsets,
            'errors': helpers.AdminErrorList(form, formsets),
            'app_label': opts.app_label,
        }
        context.update(extra_context or {})
        return self.render_change_form(request, context, form_url=form_url,
                                       add=True)

    @csrf_protect_m
    @transaction.commit_on_success
    def change_view(self, request, object_id, extra_context=None):
        """The 'change' admin view for this model."""
        model = self.model
        opts = model._meta

        obj = self.get_object(request, unquote(object_id))

        if not self.has_change_permission(request, obj):
            raise PermissionDenied

        if obj is None:
            raise Http404(u"{name}{transblock}{key} {noexist}".format(
                name=force_unicode(opts.verbose_name),
                transblock=_("object with primary key"),
                key=escape(object_id),
                noexist=_(" does not exist.")
            ))

        if request.method == 'POST' and "_saveasnew" in request.POST:
            return self.add_view(request, form_url='../add/')

        ModelForm = self.get_form(request, obj)
        formsets = []
        if request.method == 'POST':
            form = ModelForm(request.POST, request.user, instance=obj)
            if form.is_valid():
                form_validated = True
                new_object = self.save_form(request, form, change=True)
            else:
                form_validated = False
                new_object = obj
            prefixes = {}
            self.inline_instances = check_inline_instance(self, request)
            for FormSet, inline in zip(self.get_formsets(request, new_object),
                                       self.inline_instances):
                prefix = FormSet.get_default_prefix()
                prefixes[prefix] = prefixes.get(prefix, 0) + 1
                if prefixes[prefix] != 1:
                    prefix = "%s-%s" % (prefix, prefixes[prefix])
                formset = FormSet(request.POST, request.FILES,
                                  instance=new_object, prefix=prefix,
                                  queryset=inline.queryset(request))

                formsets.append(formset)

            if all_valid(formsets) and form_validated:
                self.save_model(request, new_object, form, change=True)
                form.save_m2m()
                for formset in formsets:
                    self.save_formset(request, form, formset, change=True)

                change_message = self.construct_change_message(request, form, formsets)
                self.log_change(request, new_object, change_message)
                return self.response_change(request, new_object)

        else:
            form = self.form(user=request.user, instance=obj)
            prefixes = {}
            self.inline_instances = check_inline_instance(self, request)
            for FormSet, inline in zip(self.get_formsets(request, obj), 
                                       self.inline_instances):
                prefix = FormSet.get_default_prefix()
                prefixes[prefix] = prefixes.get(prefix, 0) + 1
                if prefixes[prefix] != 1:
                    prefix = "%s-%s" % (prefix, prefixes[prefix])
                formset = FormSet(instance=obj, prefix=prefix,
                                  queryset=inline.queryset(request))
                formsets.append(formset)

        adminForm = helpers.AdminForm(form, self.get_fieldsets(request, obj),
            self.prepopulated_fields, self.get_readonly_fields(request, obj),
            model_admin=self)
        media = self.media + adminForm.media

        inline_admin_formsets = []
        self.inline_instances = check_inline_instance(self, request)
        for inline, formset in zip(self.inline_instances, formsets):
            fieldsets = list(inline.get_fieldsets(request, obj))
            prepopulated_fields = self.get_prepopulated_fields(request, obj)
            readonly = list(inline.get_readonly_fields(request, obj))
            inline_admin_formset = helpers.InlineAdminFormSet(inline, formset,
                fieldsets, prepopulated_fields, readonly, model_admin=self)
            inline_admin_formsets.append(inline_admin_formset)
            media = media + inline_admin_formset.media

        context = {
            'title': _('Change ') + force_unicode(opts.verbose_name),
            'adminform': adminForm,
            'object_id': object_id,
            'original': obj,
            'is_popup': "_popup" in request.REQUEST,
            'media': mark_safe(media),
            'inline_admin_formsets': inline_admin_formsets,
            'errors': helpers.AdminErrorList(form, formsets),
            'app_label': opts.app_label,
        }
        context.update(extra_context or {})
        return self.render_change_form(request, context, change=True, obj=obj)

    
class SeoSiteRedirectAdmin(admin.ModelAdmin):
    model = SeoSiteRedirect
    list_display = ('redirect_url', 'seosite')
    search_fields = ['redirect_url', 'seosite__domain',]

    # make redirects require super user status to edit
    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        else:
            return False
    
    def has_add_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        else:
            return False
            
    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        else:
            return False


class UnorderedChangeList(ChangeList):
    def get_ordering(self, *args, **kwargs):
        return []


class SeoSiteFacetAdmin(admin.ModelAdmin):
    model = SeoSiteFacet
    list_select_related = True
    list_display = ('customfacet', 'seosite', 'facet_type', 'boolean_operation')
    search_fields = ['seosite__domain', 'customfacet__name',]
    raw_id_fields = ("customfacet",)
    list_filter = ['facet_type']

    def get_changelist(self, request, **kwargs):
        """
        Returns the ChangeList class for use on the changelist page.
        """
        return UnorderedChangeList 


class SeoSiteAdmin(admin.ModelAdmin):
    form = SeoSiteForm
    save_on_top = True
    filter_horizontal = ('configurations', 'google_analytics',
                         'business_units', 'ats_source_codes', 
                         'billboard_images', 'special_commitments',
                         'site_tags', 'featured_companies', )
    list_display = ('name', 'domain', 'group', )
    list_filter = ['site_tags', 'special_commitments', 'group', ]
    search_fields = ['name', 'domain', ]
    fieldsets = [
        ('Basics', {'fields': [('domain', 'name', 'group',
                                'postajob_filter_type',
                               'canonical_company')]}),
        ('Site Title and Page Headline', {'fields': [('site_title',
                                                     'site_heading',
                                                     'site_description')]}),
        ('Settings', {'fields': [('site_tags', 'special_commitments',
                                  'view_sources', )]}),
    ]

    # Disable bulk delete on this model to prevent accidental catastrophe
    def get_actions(self, request):
        actions = super(SeoSiteAdmin, self).get_actions(request)
        if request.user:
            del actions['delete_selected']
        return actions

    @csrf_protect_m
    @transaction.commit_on_success
    def add_view(self, request, form_url='', extra_context=None):
        """The 'add' admin view for this model."""
        model = self.model
        opts = model._meta

        if not self.has_add_permission(request):
            raise PermissionDenied

        ModelForm = self.get_form(request)
        formsets = []
        if request.method == 'POST':
            form = ModelForm(request.POST, request.user)
            if form.is_valid():
                new_object = self.save_form(request, form, change=False)
                form_validated = True
            else:
                form_validated = False
                new_object = self.model()
            prefixes = {}
            self.inline_instances = check_inline_instance(self, request)
            for FormSet, inline in zip(self.get_formsets(request), 
                                       self.inline_instances):
                prefix = FormSet.get_default_prefix()
                prefixes[prefix] = prefixes.get(prefix, 0) + 1
                if prefixes[prefix] != 1:
                    prefix = "%s-%s" % (prefix, prefixes[prefix])
                formset = FormSet(data=request.POST, files=request.FILES,
                                  instance=new_object,
                                  save_as_new="_saveasnew" in request.POST,
                                  prefix=prefix, queryset=inline.queryset(request))
                formsets.append(formset)
            if all_valid(formsets) and form_validated:
                self.save_model(request, new_object, form, change=False)
                form.save_m2m()
                for formset in formsets:
                    self.save_formset(request, form, formset, change=False)

                self.log_addition(request, new_object)
                return self.response_add(request, new_object)
        else:
            # Prepare the dict of initial data from the request.
            # We have to special-case M2Ms as a list of comma-separated PKs.
            initial = dict(request.GET.items())
            for k in initial:
                try:
                    f = opts.get_field(k)
                except models.FieldDoesNotExist:
                    continue
                if isinstance(f, models.ManyToManyField):
                    initial[k] = initial[k].split(",")
            form = self.form(user=request.user, initial=initial)
            prefixes = {}
            self.inline_instances = check_inline_instance(self, request)
            for FormSet, inline in zip(self.get_formsets(request),
                                       self.inline_instances):
                prefix = FormSet.get_default_prefix()
                prefixes[prefix] = prefixes.get(prefix, 0) + 1
                if prefixes[prefix] != 1:
                    prefix = "%s-%s" % (prefix, prefixes[prefix])
                formset = FormSet(instance=self.model(), prefix=prefix,
                                  queryset=inline.queryset(request))
                formsets.append(formset)

        adminForm = helpers.AdminForm(form, list(self.get_fieldsets(request)),
            self.prepopulated_fields, self.get_readonly_fields(request),
            model_admin=self)
        media = self.media + adminForm.media

        inline_admin_formsets = []
        self.inline_instances = check_inline_instance(self, request)
        for inline, formset in zip(self.inline_instances, formsets):
            fieldsets = list(inline.get_fieldsets(request))
            readonly = list(inline.get_readonly_fields(request))
            inline_admin_formset = helpers.InlineAdminFormSet(inline, formset,
                fieldsets, readonly, model_admin=self)
            inline_admin_formsets.append(inline_admin_formset)
            media = media + inline_admin_formset.media

        context = {
            'title': _('Add ') + force_unicode(opts.verbose_name),
            'adminform': adminForm,
            'is_popup': "_popup" in request.REQUEST,
            'show_delete': False,
            'media': mark_safe(media),
            'inline_admin_formsets': inline_admin_formsets,
            'errors': helpers.AdminErrorList(form, formsets),
            #'root_path': self.admin_site.root_path,
            'app_label': opts.app_label,
        }
        context.update(extra_context or {})
        return self.render_change_form(request, context, form_url=form_url,
                                       add=True)

    @csrf_protect_m
    @transaction.commit_on_success
    def change_view(self, request, object_id, extra_context=None):
        """The 'change' admin view for this model."""
        model = self.model
        opts = model._meta

        obj = self.get_object(request, unquote(object_id))

        if not self.has_change_permission(request, obj):
            raise PermissionDenied

        if obj is None:
            raise Http404(u"{name}{transblock}{key} {noexist}".format(
                name=force_unicode(opts.verbose_name),
                transblock=_("object with primary key"),
                key=escape(object_id),
                noexist=_(" does not exist.")
            ))

        if request.method == 'POST' and "_saveasnew" in request.POST:
            return self.add_view(request, form_url='../add/')

        ModelForm = self.get_form(request, obj)
        formsets = []
        if request.method == 'POST':
            form = ModelForm(request.POST, request.user, instance=obj)
            if form.is_valid():
                form_validated = True
                new_object = self.save_form(request, form, change=True)
            else:
                form_validated = False
                new_object = obj
            prefixes = {}
            self.inline_instances = check_inline_instance(self, request)
            for FormSet, inline in zip(self.get_formsets(request, new_object),
                                       self.inline_instances):
                prefix = FormSet.get_default_prefix()
                prefixes[prefix] = prefixes.get(prefix, 0) + 1
                if prefixes[prefix] != 1:
                    prefix = "%s-%s" % (prefix, prefixes[prefix])
                formset = FormSet(request.POST, request.FILES,
                                  instance=new_object, prefix=prefix,
                                  queryset=inline.queryset(request))

                formsets.append(formset)

            if all_valid(formsets) and form_validated:
                self.save_model(request, new_object, form, change=True)
                form.save_m2m()
                for formset in formsets:
                    self.save_formset(request, form, formset, change=True)

                change_message = self.construct_change_message(request, form, formsets)
                self.log_change(request, new_object, change_message)
                return self.response_change(request, new_object)

        else:
            form = self.form(user=request.user, instance=obj)
            prefixes = {}
            self.inline_instances = check_inline_instance(self, request)
            for FormSet, inline in zip(self.get_formsets(request, obj), 
                                       self.inline_instances):
                prefix = FormSet.get_default_prefix()
                prefixes[prefix] = prefixes.get(prefix, 0) + 1
                if prefixes[prefix] != 1:
                    prefix = "%s-%s" % (prefix, prefixes[prefix])
                formset = FormSet(instance=obj, prefix=prefix,
                                  queryset=inline.queryset(request))
                formsets.append(formset)

        adminForm = helpers.AdminForm(form, self.get_fieldsets(request, obj),
            self.prepopulated_fields, self.get_readonly_fields(request, obj),
            model_admin=self)
        media = self.media + adminForm.media

        inline_admin_formsets = []
        self.inline_instances = check_inline_instance(self, request)
        for inline, formset in zip(self.inline_instances, formsets):
            fieldsets = list(inline.get_fieldsets(request, obj))
            readonly = list(inline.get_readonly_fields(request, obj))
            inline_admin_formset = helpers.InlineAdminFormSet(inline, formset,
                fieldsets, readonly, model_admin=self)
            inline_admin_formsets.append(inline_admin_formset)
            media = media + inline_admin_formset.media

        context = {
            'title': _('Change ') + force_unicode(opts.verbose_name),
            'adminform': adminForm,
            'object_id': object_id,
            'original': obj,
            'is_popup': "_popup" in request.REQUEST,
            'media': mark_safe(media),
            'inline_admin_formsets': inline_admin_formsets,
            'errors': helpers.AdminErrorList(form, formsets),  
            'app_label': opts.app_label,
        }
        context.update(extra_context or {})
        return self.render_change_form(request, context, change=True, obj=obj)    

    def queryset(self, request):
        qs = super(SeoSiteAdmin, self).queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(group__in=request.user.groups.all())
        
    def has_add_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        else:
            return False
            
    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        else:
            return False

    @check_message_queue
    def delete_model(self, *args, **kwargs):
        super(SeoSiteAdmin, self).delete_model(*args, **kwargs)

    @check_message_queue
    def save_model(self, *args, **kwargs):
        super(SeoSiteAdmin, self).save_model(*args, **kwargs)


class CompanyAdmin(admin.ModelAdmin):
    form = CompanyForm
    save_on_top = True
    filter_horizontal = ('job_source_ids', 'prm_saved_search_sites')
    list_display = ('name', 'featured_on','company_user_count')
    list_filter = ('enhanced', 'digital_strategies_customer')
    search_fields = ['name', 'seosite__name', 'seosite__domain']
    fieldsets = [
        ('Basics', {'fields': [('name'), ('company_slug'), ('member'),
                               ('enhanced'), ('digital_strategies_customer')]}),
        ('Company Info',{'fields':[('logo_url'),('linkedin_id'),
                                   ('canonical_microsite'),
                                   ('og_img')]}),
        ('Job Sources', {'fields': ['job_source_ids']}),
        ('Featured on', {'fields': ['sites']}),
        ('PRM', {'fields': ['prm_saved_search_sites']}),
    ]


class SpecialCommitmentAdmin(admin.ModelAdmin):
    form = SpecialCommitmentForm
    save_on_top = True
    #filter_horizontal = ('job_source_ids',)
    list_display = ('name', 'commit' , 'committed_sites')
    search_fields = ['name', 'seosite__name', 'seosite__domain']
    fieldsets = [
        ('Basics', {'fields': [('name', 'commit')]}),
        ('Sites Commited', {'fields': ['sites']}),
    ]


class SiteTagAdmin(admin.ModelAdmin):
    form = SiteTagForm 
    save_on_top = True
    fieldsets = [
        (None, {'fields': ['site_tag', 'tag_navigation',
                           ('is_site_family', 'parent')]}),
    ]


class GoogleAnalyticsCampaignAdmin(admin.ModelAdmin):
    form = GoogleAnalyticsCampaignForm
    save_on_top = True
    list_display = ('name', 'sites')
    search_fields = ['name', 'seosite__name', 'seosite__domain']
    fieldsets = [
        ('Basics', {'fields': ['name', 'group', 'campaign_source',
                               'campaign_medium', 'campaign_name',
                               'campaign_term', 'campaign_content']}),
        ('Sites', {'fields': ['sites']}),
    ]


class ATSSourceCodeAdmin(admin.ModelAdmin):
    form = ATSSourceCodeForm
    save_on_top = True
    list_display = ('name', 'sites')
    search_fields = ['name', 'seosite__name', 'seosite__domain']
    fieldsets = [
        ('Basics', {'fields': ['name','value','group','ats_name']}),
        ('Sites', {'fields': ['sites']}),
    ]


class ViewSourceAdmin(admin.ModelAdmin):
    form = ViewSourceForm
    save_on_top = True
    list_display = ('name', 'view_source' , 'sites')
    search_fields = ['name', 'view_source', 'seosite__name', 'seosite__domain']
    fieldsets = [
        ('Basics', {'fields': [('name', 'view_source')]}),
        ('Sites Commited', {'fields': ['sites']}),
    ]

admin.site.register(CustomFacet, CustomFacetAdmin)
admin.site.register(Configuration, ConfigurationAdmin)
admin.site.register(BusinessUnit, BusinessUnitAdmin)
admin.site.register(GoogleAnalytics, GoogleAnalyticsAdmin)
admin.site.register(SeoSite, SeoSiteAdmin)
admin.site.register(SeoSiteRedirect, SeoSiteRedirectAdmin)
admin.site.register(SeoSiteFacet, SeoSiteFacetAdmin)
admin.site.register(SpecialCommitment, SpecialCommitmentAdmin)
admin.site.register(SiteTag, SiteTagAdmin)
admin.site.register(GoogleAnalyticsCampaign, GoogleAnalyticsCampaignAdmin)
admin.site.register(ATSSourceCode, ATSSourceCodeAdmin)
admin.site.register(ViewSource, ViewSourceAdmin)
admin.site.register(BillboardImage, BillboardImageAdmin)
admin.site.register(Company, CompanyAdmin)

try:
    admin.site.unregister(FlatPage)
except NotRegistered:
    pass
admin.site.register(CustomPage, CustomPageAdmin)
try:
    admin.site.unregister(Site)
except NotRegistered:
    pass


def check_inline_instance(obj, req):
    """
    This method checks if the inline_instances attribute is set. If it is not, 
    it calls get_inline_instances and eturns the value to the callling location.
    If it is set, it returns the existing value. This is neededed because of a 
    change in Django 1.4 that modified when this attribute is available. 
    12/5/12 Jason Sole.
    
    Inputs:
        :obj:   The object to test. Usually "self"
        :req:   Django request object
    Returns:
        obj.inline_instances object
        
    """
    if not hasattr(obj, 'inline_instances'):
        return obj.get_inline_instances(req)
    else:
        return obj.inline_instances


def copy_to_qc(modeladmin, request, queryset):
    # This shouldnt't be used to copy a large number of objects at once.
    if queryset.count() > 5:
        error_message = 'You cannot copy more than 5 items at once.'
        modeladmin.message_user(request, error_message)
        return

    queue = copy_following_relationships(queryset, copy_to='qc-redirect')

    modeladmin.message_user(request, 'Below is a summary of the items copied. '
                                     'Any errors encountered during the '
                                     'process are included.')

    for queue_entry in queue.values():
        obj = queue_entry['object']
        related_objects = (queue_entry['foreign_keys'] +
                           queue_entry['many_to_manys'] +
                           queue_entry['null_foreign_keys'])
        related_objects = [str(related_obj) for related_obj in related_objects]
        errors = queue_entry['error']

        entry_msg = ("Object: {object}</br>"
                     "Additional objects copied because of this object: "
                     "{related_objects}</br>"
                     "Errors copying the object: {errors}")
        entry_msg = entry_msg.format(object=obj,
                                     related_objects=related_objects,
                                     errors=errors)
        modeladmin.message_user(request, mark_safe(entry_msg))


admin.site.add_action(copy_to_qc, 'Copy to QC')
