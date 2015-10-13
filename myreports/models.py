import json
from django.core.files.base import ContentFile
from django.db import models
from django.db.models.loading import get_model

from myreports.helpers import serialize, determine_user_type
from mypartners.models import SearchParameterManager


class Report(models.Model):
    """
    Models a Report which can be serialized in various formats.

    A report instance can access it's results in three ways:
        `json`: returns a JSON string of the results
        `python`: returns a `dict` of the results
        `queryset`: returns a queryset obtained by re-running `from_search`
                    with the report's parameters. Useful for when you need to
                    use attributes from a related model's instances (eg.
                    `referrals` from the `ContactRecord` model).
    """
    name = models.CharField(max_length=50)
    created_by = models.ForeignKey(
        'myjobs.User', null=True, on_delete=models.SET_NULL)
    owner = models.ForeignKey('seo.Company')
    created_on = models.DateTimeField(auto_now_add=True)
    order_by = models.CharField(max_length=50, blank=True, default='')
    app = models.CharField(default='mypartners', max_length=50)
    model = models.CharField(default='contactrecord', max_length=50)
    # included columns and sort order
    values = models.CharField(max_length=500, default='[]')
    # json encoded string of the filters used to filter
    filters = models.TextField(default="{}")
    results = models.FileField(upload_to='reports')

    company_ref = 'owner'

    objects = SearchParameterManager()

    def __init__(self, *args, **kwargs):
        super(Report, self).__init__(*args, **kwargs)
        self._results = '{}'

        if self.results:
            try:
                self._results = self.results.read()
            except IOError:
                # If we are here, the file can't be found, which is usually the
                # case when testing locally and pointing to
                # QC/Staging/Production.
                pass

    @property
    def json(self):
        return self._results

    @property
    def python(self):
        return json.loads(self._results)

    @property
    def queryset(self):
        model = get_model(self.app, self.model)
        return model.objects.from_search(self.owner, self.filters)

    def __unicode__(self):
        return self.name

    def regenerate(self):
        """Regenerate the report file if it doesn't already exist on disk."""
        contents = serialize('json', self.queryset)
        results = ContentFile(contents)

        if self.results:
            self.results.delete()

        self.results.save('%s-%s.json' % (self.name, self.pk), results)
        self._results = contents


class UserTypeManager(models.Manager):
    def for_user(self, user):
        user_type = determine_user_type(user)
        if user_type is None:
            return None
        return UserType.objects.filter(user_type=user_type,
                                       is_active=True).first()


class UserType(models.Model):
    user_type = models.CharField(max_length=10)
    is_active = models.BooleanField(default=False)
    reporting_types = models.ManyToManyField(
        'ReportingType', through='UserReportingTypes')
    objects = UserTypeManager()


class ReportingTypeManager(models.Manager):
    def active_for_user(self, user):
        user_type = UserType.objects.for_user(user)
        return (ReportingType.objects.filter(is_active=True)
                .filter(userreportingtypes__is_active=True,
                        userreportingtypes__user_type=user_type))


class ReportingType(models.Model):
    reporting_type = models.CharField(max_length=50)
    description = models.CharField(max_length=500)
    report_types = models.ManyToManyField(
        'ReportType', through='ReportingTypeReportTypes')
    is_active = models.BooleanField(default=False)
    objects = ReportingTypeManager()


class UserReportingTypes(models.Model):
    user_type = models.ForeignKey('UserType')
    reporting_type = models.ForeignKey('ReportingType')
    is_active = models.BooleanField(default=False)


class ReportTypeManager(models.Manager):
    def active_for_reporting_type(self, reporting_type):
        query_filter = dict(
            is_active=True,
            reportingtypereporttypes__reporting_type=reporting_type,
            reportingtypereporttypes__is_active=True)
        return ReportType.objects.filter(**query_filter)


class ReportType(models.Model):
    report_type = models.CharField(max_length=50)
    description = models.CharField(max_length=500)
    data_types = models.ManyToManyField(
        'DataType', through='ReportTypeDataTypes')
    is_active = models.BooleanField(default=False)
    objects = ReportTypeManager()


class ReportingTypeReportTypes(models.Model):
    reporting_type = models.ForeignKey('ReportingType')
    report_type = models.ForeignKey('ReportType')
    is_active = models.BooleanField(default=False)


class DataType(models.Model):
    data_type = models.CharField(max_length=100)
    description = models.CharField(max_length=500)
    is_active = models.BooleanField(default=False)


class ReportTypeDataTypes(models.Model):
    report_type = models.ForeignKey('ReportType')
    data_type = models.ForeignKey('DataType')
    is_active = models.BooleanField(default=False)


class Configuration(models.Model):
    name = models.CharField(max_length=50)
    is_active = models.BooleanField(default=False)


class ReportPresentation(models.Model):
    report_data = models.ForeignKey('ReportTypeDataTypes')
    presentation_type = models.ForeignKey('PresentationType')
    configuration = models.ForeignKey('Configuration')
    display_name = models.CharField(max_length=50)
    is_active = models.BooleanField(default=False)


class PresentationType(models.Model):
    presentation_type = models.CharField(max_length=100)
    description = models.CharField(max_length=500)
    is_active = models.BooleanField(default=False)


class Column(models.Model):
    app_name = models.CharField(max_length=50, null=True)
    model_name = models.CharField(max_length=50, null=True)
    column_name = models.CharField(max_length=50)
    is_active = models.BooleanField(default=False)


class InterfaceElementType(models.Model):
    interface_element_type = models.CharField(max_length=50)
    description = models.CharField(max_length=500)
    element_code = models.CharField(max_length=2000)
    is_active = models.BooleanField(default=False)


class ColumnFormat(models.Model):
    name = models.CharField(max_length=50)
    format_code = models.CharField(max_length=2000)
    is_active = models.BooleanField(default=False)


class ConfigurationColumnFormats(models.Model):
    column_format = models.ForeignKey('ColumnFormat')
    configuration_column = models.ForeignKey('ConfigurationColumn')
    is_active = models.BooleanField(default=False)


class ConfigurationColumn(models.Model):
    configuration = models.ForeignKey(Configuration)
    column = models.ForeignKey(Column, null=True)
    interface_element_type = models.ForeignKey(InterfaceElementType)
    alias = models.CharField(max_length=100)
    multi_value_expansion = models.PositiveSmallIntegerField()
    filter_only = models.BooleanField(default=False)
    default_value = models.CharField(max_length=500, blank=True, default="")
    column_formats = models.ManyToManyField(
        'ColumnFormat', through='ConfigurationColumnFormats')
    is_active = models.BooleanField(default=False)


class DynamicReport(models.Model):
    """
    Models a Report which was generated from a Configuration.

    The report can be serialized in various formats.

    A report instance can access it's results in three ways:
        `json`: returns a JSON string of the results
        `python`: returns a `dict` of the results
        `queryset`: returns a queryset obtained by re-running `from_search`
                    with the report's parameters. Useful for when you need to
                    use attributes from a related model's instances (eg.
                    `referrals` from the `ContactRecord` model).
    """
    created_by = models.ForeignKey(
        'myjobs.User', null=True, on_delete=models.SET_NULL)
    created_on = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey('seo.Company')
    configuration = models.ForeignKey('myreports.Configuration')
    results = models.FileField(upload_to='reports')

    company_ref = 'owner'

    objects = SearchParameterManager()

    def __init__(self, *args, **kwargs):
        super(DynamicReport, self).__init__(*args, **kwargs)
        self._results = '{}'
        # XXX: Where will this come from?
        self.filters = {}
        # XXX: name report better
        self.name = "Dynamic Report Name"

        if self.results:
            try:
                self._results = self.results.read()
            except IOError:
                # If we are here, the file can't be found, which is usually the
                # case when testing locally and pointing to
                # QC/Staging/Production.
                pass

    @property
    def json(self):
        return self._results

    @property
    def python(self):
        return json.loads(self._results)

    @property
    def queryset(self):
        # XXX: Assumes all columns come from one model.
        fc_config = (self.configuration
                     .configurationcolumn_set
                     .filter(is_active=True,
                             column__is_active=True)
                     .first())
        model = get_model(fc_config.column.app_name,
                          fc_config.column.model_name)

        return model.objects.from_search(self.owner, self.filters)

    def regenerate(self):
        """Regenerate the report file if it doesn't already exist on disk."""
        contents = serialize('json', self.queryset)
        results = ContentFile(contents)

        if self.results:
            self.results.delete()

        self.results.save('%s-%s.json' % (self.name, self.pk), results)
        self._results = contents
