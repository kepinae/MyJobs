import hashlib

from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from django.forms import (ModelForm, ModelMultipleChoiceField, ValidationError,
                          ChoiceField)
from django.contrib.auth.models import Group
from django.core.cache import cache
from django.utils.http import urlquote

from social_links.models import SocialLink, MicrositeCarousel, SocialLinkType
from seo.models import SeoSite


def invalidate_template_cache(fragment_name, *variables):
    args = hashlib.md5()
    args.update(u':'.join([urlquote(var) for var in variables]))
    cache_key = 'template.cache.%s.%s' % (fragment_name, args.hexdigest())
    cache.delete(cache_key)

    
class MyModelMultipleChoiceField(ModelMultipleChoiceField):
    def __init__(self, queryset, cache_choices=False, required=True,
                 widget=None, label=None, initial=None,
                 help_text=None, *args, **kwargs):
        self.my_model = kwargs.pop('my_model', None)
        super(ModelMultipleChoiceField, self).__init__(queryset, None,
            cache_choices, required, widget, label, initial, help_text,
            *args, **kwargs)    

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

        
class SocialLinkForm(ModelForm):
    sites = MyModelMultipleChoiceField(SeoSite.objects.all(), my_model=SeoSite,
                                       required=False,
                                       widget=admin.widgets\
                                       .FilteredSelectMultiple('Sites', False))
    link_icon = ChoiceField(choices=SocialLinkType.icon_choices())
    
    class Meta:
        model = SocialLink
        fields = '__all__'


class SocialLinkAdmin(admin.ModelAdmin):
    form = SocialLinkForm
    filter_horizontal = ('sites',)
    list_display = ('__unicode__', 'link_url', 'link_type', 'show_sites',
                    'group')
    exclude = ('content_type', )
    list_filter = ('link_type', )
    save_on_top = True
    search_fields = ['link_title', 'group__name', 'link_url']
    actions = []

    def invalidate_cached_footer(self, request, queryset):
        for site in SeoSite.objects.filter(sociallink__in=queryset).distinct():
            invalidate_template_cache('social_links', site.domain)
    invalidate_cached_footer.short_description = ("Delete cached footer contain"
                                                  "ing these links")
    
    def queryset(self, request):
        qs = super(SocialLinkAdmin, self).queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(group__in=request.user.groups.all())
    
    def get_form(self, request, obj=None, **kwargs):
        this = super(SocialLinkAdmin, self).get_form(request, obj, **kwargs)
        my_group_fieldset = [('link_title', 'group'),
                             ('link_type', 'link_icon'),
                             'link_url', 'sites',]
        my_fieldsets = [
            ('Social Link', {'fields': [('link_title'), ('link_type',
                                                         'link_icon'),
                                        'link_url', 'sites']}),
        ]
        this.base_fields['sites'].queryset = SeoSite.objects.all()
        self.fieldsets = my_fieldsets
        if request.user.is_superuser:
            this.base_fields['link_type'].choices = (('company', 'Company'),
                                                     ('social', 'Social'),
                                                     ('directemployers',
                                                      'DirectEmployers'))
        else:
            this.base_fields['link_type'].choices = (('company', 'Company'),
                                                     ('social', 'Social'))
        this.base_fields['link_icon'].choices = SocialLinkType.icon_choices()

        if obj:
            this.base_fields['sites'].queryset = SeoSite.objects\
                                                        .filter(group=obj.group)
            this.base_fields['sites'].initial = [o.pk for o in obj.sites.filter(
                group=obj.group)]
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
                    request.user.groups.count() is 1 and not obj.group):
            obj.group = request.user.groups.all()[0]
        obj.content_type = ContentType.objects.get_for_model(SocialLink)
        obj.save()


class MicrositeCarouselForm(ModelForm):
    active_sites = MyModelMultipleChoiceField(
        SeoSite.objects.all(),
        my_model=SeoSite,
        required=False,
        widget=(admin.widgets.FilteredSelectMultiple('Sites', False))
    )
    link_sites = MyModelMultipleChoiceField(
        SeoSite.objects.all(),
        my_model=SeoSite,
        required=False,
        widget=(admin.widgets.FilteredSelectMultiple('Sites', False))
    )
    
    def save(self, commit=True):
        added_sites = set()
        msc = ModelForm.save(self, commit)
        for site in self.cleaned_data['active_sites']:
            added_sites.add(site)
        if msc.pk:
            if set(added_sites) != set(msc.seosite_set.all()):
                msc.seosite_set = added_sites
        else:
            msc.save()
            msc.seosite_set = added_sites
        return msc
    
    class Meta:
        model = MicrositeCarousel
        fields = '__all__'

class MicrositeCarouselAdmin(admin.ModelAdmin):
    form = MicrositeCarouselForm
    filter_horizontal = ('link_sites',)
    list_display = ('__unicode__', 'carousel_title', 'show_active_sites',
                    'is_active', 'group')
    
    def queryset(self, request):
        qs = super(MicrositeCarouselAdmin, self).queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(group__in=request.user.groups.all())
    
    def get_form(self, request, obj=None, **kwargs):
        this = super(MicrositeCarouselAdmin, self).get_form(request, obj,
                                                            **kwargs)
        my_group_fieldset = [('group', 'is_active'), ('carousel_title'),
                             ('link_sites', 'active_sites'),'display_rows']
        my_fieldsets = [('Social Link',
                         {'fields': [('is_active'), ('carousel_title'),
                                     ('link_sites', 'active_sites'),
                                     'display_rows']}),]
        this.base_fields['active_sites'].queryset = SeoSite.objects.all()
        self.fieldsets = my_fieldsets
        
        if obj:
            this.base_fields['active_sites'].queryset = (SeoSite.objects\
                                                         .filter(group=obj.group
                                                             ))
            this.base_fields['active_sites'].initial = [o.pk for o in
                                                        obj.seosite_set.filter(
                                                            group=obj.group)]
            this.base_fields['link_sites'].queryset = (SeoSite.objects\
                                                       .filter(group=obj.group))
            this.base_fields['link_sites'].initial = [o.pk for o in
                                                      obj.seosite_set\
                                                      .filter(group=obj.group)]
            if request.user.is_superuser or request.user.groups.count() > 1:
                if not request.user.is_superuser:
                    this.base_fields['group'].queryset = Group.objects\
                                                         .filter(id__in=request\
                                                                 .user.groups\
                                                                 .all())
                self.fieldsets[0][1]['fields'] = my_group_fieldset
                this.base_fields['group'].required = True
        else:
            this.base_fields['active_sites'].initial = []
            this.base_fields['active_sites'].queryset = SeoSite.objects\
                                                        .filter(id=None)
            this.base_fields['link_sites'].initial = []
            this.base_fields['link_sites'].queryset = SeoSite.objects\
                                                      .filter(id=None)
            if request.user.is_superuser or request.user.groups.count() > 1:
                self.fieldsets[0][1]['fields'] = my_group_fieldset
                this.base_fields['group'].required = True
                
                if not request.user.is_superuser:
                    this.base_fields['group'].queryset = (
                        Group.objects.filter(id__in=request.user.groups.all())
                    )
        return this
    
    def save_model(self, request, obj, form, change):
        if (not request.user.is_superuser and
            request.user.groups.count() is 1 and
            not obj.group):
            obj.group = request.user.groups.all()[0]
        if obj.is_active:
            #Force an evaluation of obj site keys. When obj.seosite_set was used
            #in queries for qs, an error would be thrown if the two objects had
            #been queried from different databases
            obj_site_keys = [site.pk for site in obj.seosite_set.all()]
            qs = MicrositeCarousel.objects.filter(seosite__pk__in=obj_site_keys, 
                                                  is_active=1)
            if obj.pk:
                qs = qs.exclude(pk=obj.pk)
            if qs.count() != 0:
                qs[0].seosite_set = (set(qs[0].seosite_set.all()) -
                                     set(obj.seosite_set.all()))
        obj.save()


admin.site.register(SocialLink, SocialLinkAdmin)
admin.site.register(MicrositeCarousel, MicrositeCarouselAdmin)
admin.site.register(SocialLinkType)
