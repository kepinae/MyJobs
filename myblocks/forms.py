from fsm.widget import FSM

from django import forms
from django.core.urlresolvers import reverse_lazy

from myblocks import models


class BlockForm(forms.ModelForm):
    class Meta:
        exclude = ('updated', )
        model = models.Block

    def __init__(self, *args, **kwargs):
        super(BlockForm, self).__init__(*args, **kwargs)
        self.fields['template'].initial = models.raw_base_template(self.Meta.model)
        self.fields['head'].initial = models.raw_base_head(self.Meta.model)


class ApplyLinkBlockForm(BlockForm):
    class Meta:
        model = models.ApplyLinkBlock
        fields = '__all__'


class BreadboxBlockForm(BlockForm):
    class Meta:
        model = models.BreadboxBlock
        fields = '__all__'


class ColumnBlockForm(forms.ModelForm):
    class Meta:
        exclude = ('updated', 'template', )
        model = models.ColumnBlock


class ContentBlockForm(BlockForm):
    class Meta:
        model = models.ContentBlock
        fields = '__all__'


class FacetBlurbBlockForm(BlockForm):
    class Meta:
        model = models.FacetBlurbBlock
        fields = '__all__'


class JobDetailBlockForm(BlockForm):
    class Meta:
        model = models.JobDetailBlock
        fields = '__all__'


class JobDetailBreadboxBlockForm(BlockForm):
    class Meta:
        model = models.JobDetailBreadboxBlock
        fields = '__all__'


class JobDetailHeaderBlockForm(BlockForm):
    class Meta:
        model = models.JobDetailHeaderBlock
        fields = '__all__'


class LoginBlockForm(BlockForm):
    class Meta:
        model = models.LoginBlock
        fields = '__all__'


class MoreButtonBlockForm(BlockForm):
    class Meta:
        model = models.MoreButtonBlock
        fields = '__all__'


class RegistrationBlockForm(BlockForm):
    class Meta:
        model = models.RegistrationBlock
        fields = '__all__'


class SavedSearchWidgetBlockForm(BlockForm):
    class Meta:
        model = models.SavedSearchWidgetBlock
        fields = '__all__'


class SearchBoxBlockForm(BlockForm):
    class Meta:
        model = models.SearchBoxBlock
        fields = '__all__'


class SearchFilterBlockForm(BlockForm):
    class Meta:
        model = models.SearchFilterBlock
        fields = '__all__'


class SearchResultBlockForm(BlockForm):
    class Meta:
        model = models.SearchResultBlock
        fields = '__all__'


class SearchResultHeaderBlockForm(BlockForm):
    class Meta:
        model = models.SearchResultBlock
        fields = '__all__'


class ShareBlockForm(BlockForm):
    class Meta:
        model = models.ShareBlock
        fields = '__all__'


class VeteranSearchBoxForm(BlockForm):
    class Meta:
        model = models.VeteranSearchBox
        fields = '__all__'


class PageForm(forms.ModelForm):
    class Meta:
        exclude = ('updated', )
        widgets = {
            'sites': FSM('Site', reverse_lazy('site_admin_fsm'), lazy=True),
        }
        model = models.Page

    def __init__(self, *args, **kwargs):
        super(PageForm, self).__init__(*args, **kwargs)
        self.fields['head'].initial = models.raw_base_head(self.Meta.model)


class RowForm(forms.ModelForm):
    class Meta:
        exclude = ('updated', )
        model = models.Row
