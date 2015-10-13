from collections import OrderedDict
from datetime import datetime
import json

from django.core.files.base import ContentFile
from django.db.models.loading import get_model
from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.utils.decorators import method_decorator
from django.views.generic import View
from django.views.decorators.http import require_http_methods

from myreports.helpers import humanize, serialize
from myreports.models import (
    Report, ReportingType, ReportType, Configuration, DynamicReport)
from postajob import location_data
from universal.helpers import get_company_or_404
from universal.decorators import has_access


@has_access('prm')
def overview(request):
    """The Reports app landing page."""
    company = get_company_or_404(request)

    success = 'success' in request.POST
    reports = Report.objects.filter(owner=company).order_by("-created_on")
    report_count = reports.count()
    past_reports = reports[:10]
    states = OrderedDict(
        sorted((v, k) for k, v in location_data.states.inv.iteritems()))

    ctx = {
        "company": company,
        "success": success,
        "states": json.dumps(states),
        "past_reports": past_reports,
        "report_count": report_count
    }

    if request.is_ajax():
        response = HttpResponse()
        html = render_to_response('myreports/includes/report_overview.html',
                                  ctx, RequestContext(request)).content
        response.content = html
        return response

    return render_to_response('myreports/reports.html', ctx,
                              RequestContext(request))


@has_access('prm')
def report_archive(request):
    """Archive of previously run reports."""
    if request.is_ajax():
        company = get_company_or_404(request)
        reports = Report.objects.filter(owner=company).order_by("-created_on")

        ctx = {
            "reports": reports
        }

        response = HttpResponse()
        html = render_to_response('myreports/includes/report-archive.html',
                                  ctx, RequestContext(request))
        response.content = html.content

        return response


@has_access('prm')
def view_records(request, app="mypartners", model="contactrecord"):
    """
    Returns records as JSON.

    Inputs:
        :request: Request object to inspect for search parameters.
        :app: Application to query.
        :model: Model to query.

    Query String Parameters:
        :filters: A JSON string representing th exact query to be run.
        :values: The fields to include in the output.
        :order_by: The field to order the results by. Prefix with a '-' to
                   indiciate descending order.

    Output:
       A JSON response containing the records queried for.
    """
    if request.is_ajax() and request.method == 'POST':
        company = get_company_or_404(request)
        filters = request.POST.get("filters")
        values = request.POST.getlist("values")
        order_by = request.POST.get("order_by", None)

        records = get_model(app, model).objects.from_search(
            company, filters)

        if values:
            if not hasattr(values, '__iter__'):
                values = [values]

            records = records.values(*values)

        if order_by:
            if not hasattr(order_by, '__iter__'):
                order_by = [order_by]

            records = records.order_by(*order_by)

        ctx = serialize('json', records, values=values)

        response = HttpResponse(
            ctx, content_type='application/json; charset=utf-8')

        return response
    else:
        raise Http404("This view is only reachable via an AJAX GET request.")


class ReportView(View):
    """
    View for managing report objects.

    A GET request will fetch a report, where as a POST will generate a new
    report.
    """

    app = 'mypartners'
    model = 'contactrecord'

    @method_decorator(has_access('prm'))
    def dispatch(self, *args, **kwargs):
        return super(ReportView, self).dispatch(*args, **kwargs)

    def get(self, request, **kwargs):
        """
        Get a report by ID and return interesting numbers as a JSON
        response. The only expected query parameter is 'id'.

        Query String Parameters:
            :id: The id of the report to retrieve

        Outputs:
            Renders a json object with counts for email, calls, searches,
            meetings, applications, interviews, hires, communications,
            referrals, and contacts. All these are integers except for
            contacts, which is a list of objects, each of which has a name,
            email, referral count, and communications count.
        """

        report_id = request.GET.get('id', 0)
        report = Report.objects.get(id=report_id)

        if report.model == "contactrecord":
            records = report.queryset
            ctx = json.dumps({
                'emails': records.emails,
                'calls': records.calls,
                'searches': records.searches,
                'meetings': records.meetings,
                'applications': records.applications,
                'interviews': records.interviews,
                'hires': records.hires,
                'communications': records.communication_activity.count(),
                'referrals': records.referrals,
                'contacts': list(records.contacts)})
            status = 200
        elif report.results:
            ctx = report.json
            status = 200
        else:
            ctx = "Report %s has no results. Please regenerate." % report.name
            status = 503

        return HttpResponse(
            ctx,
            status=status,
            content_type='application/json; charset=utf-8')

    def post(self, request, app='mypartners', model='contactrecords'):
        """
        Create a report by querying on a specific model.

        The request's POST data is parsed for parameters to pass to the model's
        `from_search` method.

        Inputs:
            :app: The app to which the model belongs.
            :model: The model to query on

        Query String Parameters:
            :csrfmiddlewaretoken: Used to prevent Cross Site Request Forgery.
            :report_name: What to name the report. Spaces are converted to
                          underscores.
            :filters: A JSON string representing th exact query to be run.
            :values: Fields to include in report output.

        Outputs:
           An HttpResponse indicating success or failure of report creation.
        """
        company = get_company_or_404(request)
        name = request.POST.get('report_name', str(datetime.now()))
        filters = request.POST.get('filters', "{}")

        records = get_model(app, model).objects.from_search(
            company, filters)

        contents = serialize('json', records)
        results = ContentFile(contents)
        report, _ = Report.objects.get_or_create(
            name=name, created_by=request.user,
            owner=company, app=app, model=model,
            filters=filters)

        report.results.save('%s-%s.json' % (name, report.pk), results)

        return HttpResponse(name, content_type='text/plain')


@has_access('prm')
def regenerate(request):
    """
    Regenerates a report.

    Useful if the report json file is no longer available on disk. If called
    and the report is already on disk, `Report.regenerate` does nothing.

    Query String Parameters:
        :id: ID of the report to regenerate.
    """

    if request.method == 'GET':
        report_id = request.GET.get('id', 0)
        report = get_object_or_404(
            get_model('myreports', 'report'), pk=report_id)

        report.regenerate()

        return HttpResponse("Report successfully regenerated",
                            content_type='text/csv')

    raise Http404(
        "This view is only reachable via a GET request.")


@has_access('prm')
def downloads(request):
    """ Renders a download customization screen.

        If the report has `values`, then the screen will render the checkboxes
        representing those fields as checked and all others as unchecked. The
        order of the rendered checklist follows these `values`, with all other
        checkboxes being ordered aphabetically.

        Query String Parameters:
            :id: ID of the report to show options for.
    """

    if request.is_ajax() and request.method == 'GET':
        report_id = request.GET.get('id', 0)
        report = get_object_or_404(
            get_model('myreports', 'report'), pk=report_id)

        common_blacklist = ['pk', 'approval_status']
        blacklist = {
            'contactrecord': common_blacklist,
            'contact': common_blacklist + ['archived_on', 'library', 'user'],
            'partner': common_blacklist + ['library', 'owner']}

        if report.python:
            fields = sorted([field for field in report.python[0].keys()
                             if field not in blacklist[report.model]])
        else:
            fields = []

        values = json.loads(report.values) or fields
        for field_list in [values, fields]:
            if 'contact_type' in field_list:
                index = field_list.index('contact_type')
                field_list[index] = 'communication_type'
        fields = values + [field for field in fields if field not in values]

        column_choice = ''
        sort_order = ''
        if report.order_by:
            if '-' in report.order_by:
                sort_order = '-'
                column_choice = report.order_by[1:]
            else:
                column_choice = report.order_by

        columns = OrderedDict()
        for field in fields:
            columns[' '.join(
                filter(bool, field.split('_'))).title()] = field in values

        ctx = {'columns': columns,
               'sort_order': sort_order,
               'column_choice': column_choice}

        return render_to_response('myreports/includes/report-download.html',
                                  ctx, RequestContext(request))
    else:
        raise Http404("This view is only reachable via an AJAX request")


@has_access('prm')
def download_report(request):
    """
    Download report as CSV.

    Query String Parameters:
        :id: ID of the report to download
        :values: Fields to include in the resulting CSV, as well as the order
                 in which to include them.
        :order_by: The sort order for the resulting CSV.

    Outputs:
        The report with the specified options rendered as a CSV file.
    """

    report_id = request.GET.get('id', 0)
    values = request.GET.getlist('values', None)
    order_by = request.GET.get('order_by', None)

    report = get_object_or_404(
        get_model('myreports', 'report'), pk=report_id)

    if order_by:
        report.order_by = order_by
        report.save()

    if values:
        report.values = json.dumps(values)
        report.save()

    records = humanize(report.python)

    response = HttpResponse(content_type='text/csv')
    content_disposition = "attachment; filename=%s-%s.csv"
    response['Content-Disposition'] = content_disposition % (
        report.name.replace(' ', '_'), report.pk)

    response.write(serialize('csv', records, values=values, order_by=order_by))

    return response


@has_access('prm')
@require_http_methods(['GET'])
def dynamicoverview(request):
    """The Dynamic Reports page."""
    company = get_company_or_404(request)
    states = OrderedDict(
        sorted((v, k) for k, v in location_data.states.inv.iteritems()))

    ctx = {
        "company": company,
        "states": json.dumps(states),
    }

    return render_to_response('myreports/dynamicreports.html', ctx,
                              RequestContext(request))


@has_access('prm')
@require_http_methods(['POST'])
def reporting_types_api(request):
    reporting_types = (ReportingType.objects
                       .active_for_user(request.user))

    def entry(reporting_type):
        return (str(reporting_type.id),
                {'name': reporting_type.reporting_type,
                 'description': reporting_type.description})

    data = {'reporting_type':
            dict(entry(rt) for rt in reporting_types)}
    return HttpResponse(content_type='application/json',
                        content=json.dumps(data))


@has_access('prm')
@require_http_methods(['POST'])
def report_types_api(request):

    reporting_type_id = request.POST['reporting_type_id']
    report_types = (ReportType.objects
                    .active_for_reporting_type(reporting_type_id))

    def entry(report_type):
        return (str(report_type.id),
                {'name': report_type.report_type,
                 'description': report_type.description})

    data = {'report_type':
            dict(entry(rt) for rt in report_types)}
    return HttpResponse(content_type='application/json',
                        content=json.dumps(data))


@has_access('prm')
@require_http_methods(['POST'])
def run_dynamic_report(request):
    config_id = request.POST['configuration_id']
    config = Configuration.objects.get(id=config_id)

    company = request.user.companyuser_set.first().company

    report = DynamicReport.objects.create(
        configuration=config,
        owner=company)

    report.regenerate()
    report.save()

    data = {'id': report.id}
    return HttpResponse(content_type='application/json',
                        content=json.dumps(data))


@has_access('prm')
@require_http_methods(['GET'])
def download_dynamic_report(request):
    """
    Download dynamic report as CSV.

    Query String Parameters:
        :id: ID of the report to download
        :values: Fields to include in the resulting CSV, as well as the order
                 in which to include them.
        :order_by: The sort order for the resulting CSV.

    Outputs:
        The report with the specified options rendered as a CSV file.
    """

    report_id = request.GET.get('id', 0)
    values = request.GET.getlist('values', None)
    order_by = request.GET.get('order_by', None)

    report = DynamicReport.objects.get(id=report_id)

    if order_by:
        report.order_by = order_by
        report.save()

    if values:
        report.values = json.dumps(values)
        report.save()

    records = humanize(report.python)

    response = HttpResponse(content_type='text/csv')
    content_disposition = "attachment; filename=%s-%s.csv"
    response['Content-Disposition'] = content_disposition % (
        report.name.replace(' ', '_'), report.pk)

    response.write(serialize('csv', records, values=values, order_by=order_by))

    return response
