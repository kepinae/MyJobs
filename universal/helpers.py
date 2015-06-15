from copy import copy
import re
import urllib
from urlparse import parse_qsl, urlparse, urlunparse

from django.db.models.loading import get_model
from django.conf import settings
from django.shortcuts import get_object_or_404, Http404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.mail import EmailMessage


def update_url_param(url, param, new_val):
    """
    Changes the value for a parameter in a query string. If the parameter
    wasn't already in the query string, it adds it.

    inputs:
    :url: The url containing the query string to be updated.
    :param: The param to be changed.
    :new_val: The value to update the param with.

    outputs:
    The new url.
    """

    url_parts = list(urlparse(url))
    parts = copy(url_parts)
    query = {k.encode('utf-8'): v.encode('utf-8')
             for k, v in parse_qsl(parts[4])}
    query[param] = new_val
    parts[4] = urllib.urlencode(query)

    return urlunparse(parts)


def build_url(reverse_url, params):
    return '%s?%s' % (reverse_url, urllib.urlencode(params))


def get_int_or_none(string):
    try:
        return int(string)
    except (ValueError, TypeError, UnicodeEncodeError):
        return None


def get_domain(url):
    """
    Attempts to determine the domain from a url with unknown formatting.

    Created because urlparse.urlparse doesn't handle urls with a
    missing protocol very well. Unfortunately this doesn't handle
    anything except no protocol, http, or https at all.

    """
    pattern = '(http://|https://)?([^/]*\.)?(?P<domain>[^/]*\.[^/]*)'
    pattern = re.compile(pattern)
    try:
        return pattern.search(url).groupdict()['domain'].split("/")[0]
    except (AttributeError, KeyError, TypeError):
        return None


def sequence_to_dict(from_):
    """
    Turns a sequence of repeated key, value elements into a dict. The input
    sequence will be truncated at the last odd index.

    This was originally intended to be used to turn faceted fields returned by
    Solr into a dictionary. These lists are of the form
    ['field_name', facet_count]

    Examples:
    list_to_dict([]) => {}
    list_to_dict(['key_1', 1]) => {'key_1': 1}
    list_to_dict(['key_1', 'value_1', 'key_2']) => {'key_1', 'value_1'}

    Inputs:
    :from_: Sequence to be converted

    Output:
        Dictionary created from the input sequence
    """
    return dict(zip(*[iter(from_)] * 2))


def get_company(request):
    """
    Uses the myjobs_company cookie to determine what the current company is.

    """
    if not request.user or request.user.is_anonymous():
        return None

    # If settings.SITE is set we're on a microsite, so get the company
    # based on the microsite we're on instead.
    if settings.SITE.canonical_company:
        company = settings.SITE.canonical_company

        if company.companyuser_set.filter(user=request.user).exists():
            return company

    # If the current hit is for a non-microsite admin, we don't know what
    # company we should be using; don't guess.
    if request.get_full_path().startswith('/admin/'):
        return None

    company = request.COOKIES.get('myjobs_company')
    if company:
        company = get_object_or_404(get_model('seo', 'company'), pk=company)

        # If the company cookie is correctly set, confirm that the user
        # actually has access to that company.
        if company not in request.user.get_companies():
            company = None

    if not company:
        try:
            # If the company cookie isn't set, then the user should have
            # only one company, so use that one.
            company = request.user.get_companies()[0]
        except IndexError:
            company = None
    return company


def get_company_or_404(request):
    """ Simple wrapper around get_company that raises Http404 if no valid
        company is found.
    """
    company = get_company(request)

    if not company:
        raise Http404
    else:
        return company


def get_object_or_none(model, **kwargs):
    try:
        return model.objects.get(**kwargs)
    except (model.DoesNotExist, ValueError):
        return None


def add_pagination(request, object_list, per_page=None):
    """
    Basic Django Pagination -- Pass a list of objects you wish to paginate.
    That listing will be wrapped by the Paginator object then the listing will
    get split into Pages deemed by :objects_per_page:, which is defaulted
    to 10.

    Inputs:
    :object_list:   A list (or Queryset) of an object you wish to paginate.
    :per_page:      Number of objects per page.

    Outputs:
        Returns a Paginator Object. Paginator acts as a wrapper for the object
        list you pass through. The objects and their attributes are still
        accessed the same but has added methods for the paginator and the
        pages that are created.

    """
    try:
        objects_per_page = int(request.GET.get('per_page') or 10)
    except ValueError:
        objects_per_page = 10
    page = request.GET.get('page')
    paginator = Paginator(object_list, per_page or objects_per_page)

    try:
        pagination = paginator.page(page)
    except PageNotAnInteger:
        pagination = paginator.page(1)
    except EmptyPage:
        pagination = paginator.page(paginator.num_pages)

    return pagination


def has_mx_record(domain):
    return True


def send_email(email_body, email_type=settings.GENERIC,
               recipients=None, site=None, headers=None, **kwargs):
    recipients = recipients or []

    company_name = 'My.jobs'
    domain = 'my.jobs'

    if site:
        domain = site.email_domain
        if site.canonical_company:
            company_name = site.canonical_company.name

    kwargs['company_name'] = company_name
    kwargs['domain'] = domain.lower()

    sender = settings.EMAIL_FORMATS[email_type]['address']
    sender = sender.format(**kwargs)

    # Capitalize domain for display purposes.
    kwargs['domain'] = kwargs['domain'].lower()
    subject = settings.EMAIL_FORMATS[email_type]['subject']
    subject = subject.format(**kwargs)

    email_kwargs = {
        'subject': subject, 'body': email_body, 'from_email': sender,
        'to': recipients
    }
    if headers is not None:
        email_kwargs['headers'] = headers
    message = EmailMessage(**email_kwargs)
    message.content_subtype = 'html'
    message.send()

    return message
