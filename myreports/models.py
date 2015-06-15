import json
from django.core.files.base import ContentFile
from django.db import models
from django.db.models.loading import get_model

from myreports.helpers import serialize
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
    # json encoded string of the params used to filter
    params = models.TextField()
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
                self.results.delete()

    @property
    def json(self):
        return self._results

    @property
    def python(self):
        return json.loads(self._results)

    @property
    def queryset(self):
        model = get_model(self.app, self.model)
        params = json.loads(self.params)
        return model.objects.from_search(self.owner, params)

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
