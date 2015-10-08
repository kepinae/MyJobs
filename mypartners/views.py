from datetime import date, timedelta
from email.parser import HeaderParser
from email.utils import getaddresses
from itertools import chain
import json
from lxml import etree
import pytz
import re
import unicodecsv
from urllib import urlencode
from validate_email import validate_email

from django.conf import settings
from django.contrib.auth.decorators import user_passes_test
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.core.files.storage import default_storage
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.utils.html import strip_tags
from django.utils.text import force_text
from django.utils.timezone import localtime, now
from django.utils.datastructures import SortedDict
from django.views.decorators.csrf import csrf_exempt
from urllib2 import HTTPError

from email_parser import build_email_dicts, get_datetime_from_str
from universal.helpers import (get_company_or_404, get_int_or_none,
                               add_pagination, get_object_or_none)
from universal.decorators import company_has_access, warn_when_inactive
from myjobs.models import User
from mysearches.models import PartnerSavedSearch
from mysearches.helpers import get_interval_from_frequency
from mysearches.forms import PartnerSavedSearchForm
from mypartners.forms import (PartnerForm, ContactForm,
                              NewPartnerForm, ContactRecordForm, TagForm,
                              LocationForm)
from mypartners.models import (Partner, Contact, ContactRecord,
                               PRMAttachment, ContactLogEntry, Tag,
                               CONTACT_TYPE_CHOICES, ADDITION, DELETION,
                               Location)
from mypartners.helpers import (prm_worthy, add_extra_params,
                                add_extra_params_to_jobs, log_change,
                                contact_record_val_to_str, retrieve_fields,
                                get_records_from_request,
                                filter_partners,
                                new_partner_from_library,
                                send_contact_record_email_response,
                                find_partner_from_email, tag_get_or_create)


@warn_when_inactive(feature='Partner Relationship Manager is')
@company_has_access('member')
def prm(request):
    """
    Partner Relationship Manager

    """
    company = get_company_or_404(request)

    partners = filter_partners(request)
    paginator = add_pagination(request, partners) if partners else None

    if request.is_ajax():
        ctx = {
            'partners': paginator,
            'on_page': 'prm',
            'ajax': 'true',
        }
        response = HttpResponse()
        html = render_to_response('mypartners/includes/partner_column.html',
                                  ctx, RequestContext(request))
        response.content = html.content
        return response

    ctx = {
        'has_partners': True if paginator else False,
        'partners': paginator,
        'company': company,
        'user': request.user,
        'partner_ct': ContentType.objects.get_for_model(Partner).id,
        'view_name': 'PRM',
    }

    return render_to_response('mypartners/prm.html', ctx,
                              RequestContext(request))


@warn_when_inactive(feature='Partner Library is')
@company_has_access('member')
def partner_library(request):
    company = get_company_or_404(request)

    if request.is_ajax():
        partners = filter_partners(request, True)
        paginator = add_pagination(request, partners)
        ctx = {
            'partners': paginator,
            'on_page': 'partner_library'
        }
        response = HttpResponse()
        html = render_to_response('mypartners/includes/partner_column.html',
                                  ctx, RequestContext(request))
        response.content = html.content
        return response

    partners = filter_partners(request, True)
    paginator = add_pagination(request, partners)

    ctx = {
        'company': company,
        'view_name': 'PRM',
        'partners': paginator
    }

    return render_to_response('mypartners/partner_library.html', ctx,
                              RequestContext(request))


@company_has_access('member')
def create_partner_from_library(request):
    """ Creates a partner and contact from a library_id. """
    partner = new_partner_from_library(request)

    redirect = False
    if request.REQUEST.get("redirect"):
        redirect = True
    ctx = {
        'partner': partner.id,
        'redirect': redirect
    }

    return HttpResponse(json.dumps(ctx))


@warn_when_inactive(feature='Partner Relationship Manager is')
@company_has_access('member')
def partner_details(request):
    company, partner, user = prm_worthy(request)

    form = PartnerForm(instance=partner, auto_id=False)

    contacts = Contact.objects.filter(
        partner=partner, archived_on__isnull=True)
    contact_ct_id = ContentType.objects.get_for_model(Contact).id
    partner_ct_id = ContentType.objects.get_for_model(Partner).id

    ctx = {
        'company': company,
        'form': form,
        'contacts': contacts,
        'partner': partner,
        'contact_ct': contact_ct_id,
        'partner_ct': partner_ct_id,
        'view_name': 'PRM',
    }
    return render_to_response('mypartners/partner_details.html', ctx,
                              RequestContext(request))


@warn_when_inactive(feature='Partner Relationship Manager is')
@company_has_access('member')
def edit_item(request):
    """ Contact/Partner Form.

        If the user reaches this form thorugh the `edit_contact` URL and a
        valid partner_id is provided, they are presented with the "Add Partner"
        form.

        Conversely, if the user reaches this form through the `create_partner`
        URL, they are presented with "Add Contact" form. If a valid `item_id`
        is passed, we preload the form with that contact's information.
    """
    try:
        partner_id = int(request.REQUEST.get("partner") or 0)
        item_id = int(request.REQUEST.get('id') or 0)
        content_id = int(request.REQUEST.get('ct') or 0)
    except ValueError:
        raise Http404

    company = get_company_or_404(request)
    partners = []
    contacts = []
    if partner_id and request.path == reverse('edit_contact'):
        partner = get_object_or_404(company.partner_set.all(), id=partner_id)
        if item_id:
            item = get_object_or_404(Contact, partner=partner, pk=item_id)
            form = ContactForm(instance=item, auto_id=False)
        else:
            contacts = list(partner.contact_set.filter(
                archived_on__isnull=True).values(
                    'pk', 'name', 'email', 'phone'))
            form = ContactForm()
            item = None
    elif request.path == reverse('create_partner'):
        partner = None
        if item_id:
            item = get_object_or_404(Partner, pk=item_id)
            form = PartnerForm(instance=item)
        else:
            partners = list(company.partner_set.values(
                'pk', 'name', 'uri'))
            item = None
            form = NewPartnerForm()
    else:
        raise Http404

    ctx = {
        'form': form,
        'partner': partner,
        'partners': json.dumps(partners),
        'company': company,
        'contact': item,
        'contacts': json.dumps(contacts),
        'content_id': content_id,
        'view_name': 'PRM',
    }
    if item_id:
        ctx['locations'] = Contact.objects.get(pk=item_id).locations.all()

    return render_to_response('mypartners/edit_item.html', ctx,
                              RequestContext(request))


@company_has_access('member')
def save_init_partner_form(request):
    form = NewPartnerForm(user=request.user, data=request.POST)

    if form.is_valid():
        form.save()
        return HttpResponse(status=200)
    else:
        return HttpResponse(json.dumps(form.errors))


@company_has_access('member')
def save_item(request):
    """
    Generic save for Partner and Contact Forms.

    """
    company = get_company_or_404(request)
    content_id = int(request.REQUEST.get('ct') or 0)

    if content_id == ContentType.objects.get_for_model(Contact).id:
        item_id = request.REQUEST.get('id') or None
        try:
            partner_id = int(request.REQUEST.get('partner') or 0)
        except TypeError:
            raise Http404

        partner = get_object_or_404(company.partner_set.all(), id=partner_id)

        if item_id:
            try:
                item = Contact.objects.get(partner=partner, pk=item_id)
            except Contact.DoesNotExist:
                raise Http404
            else:
                form = ContactForm(instance=item, auto_id=False,
                                   data=request.POST)
                if form.is_valid():
                    form.save(request.user, partner)
                    return HttpResponse(status=200)
                else:
                    return HttpResponse(json.dumps(form.errors))
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save(request.user, partner)
            return HttpResponse(status=200)
        else:
            return HttpResponse(json.dumps(form.errors))

    if content_id == ContentType.objects.get_for_model(Partner).id:
        try:
            partner_id = int(request.REQUEST.get('partner'))
        except TypeError:
            raise Http404

        partner = get_object_or_404(company.partner_set.all(), id=partner_id)
        form = PartnerForm(instance=partner, auto_id=False, data=request.POST)
        if form.is_valid():
            form.save(request.user, partner)
            return HttpResponse(status=200)
        else:
            return HttpResponse(json.dumps(form.errors))


@warn_when_inactive(feature='Partner Relationship Manager is')
@company_has_access('member')
def delete_prm_item(request):
    """
    Deletes Partners and Contacts

    """
    company = get_company_or_404(request)
    partner_id = request.REQUEST.get('partner')
    partner_id = get_int_or_none(partner_id)

    item_id = request.REQUEST.get('id')
    contact_id = get_int_or_none(item_id)

    content_id = request.REQUEST.get('ct')
    content_id = get_int_or_none(content_id)

    if content_id == ContentType.objects.get_for_model(Partner).id:
        partner = get_object_or_404(Partner, id=partner_id, owner=company)
        log_change(partner, None, request.user, partner, partner.name,
                   action_type=DELETION)
        partner.archive()
        return HttpResponseRedirect(reverse('prm') + '?company=' +
                                    str(company.id))
    elif content_id == ContentType.objects.get_for_model(ContactRecord).id:
        contact_record = get_object_or_404(ContactRecord, partner=partner_id,
                                           id=item_id)
        partner = get_object_or_404(Partner, id=partner_id, owner=company)
        log_change(contact_record, None, request.user, partner,
                   contact_record.contact.name, action_type=DELETION)
        contact_record.archive()
        return HttpResponseRedirect(reverse('partner_records')+'?company=' +
                                    str(company.id)+'&partner=' +
                                    str(partner_id))
    elif content_id == ContentType.objects.get_for_model(PartnerSavedSearch).id:
        saved_search = get_object_or_404(PartnerSavedSearch, id=item_id)
        partner = get_object_or_404(Partner, id=partner_id, owner=company)
        log_change(saved_search, None, request.user, partner,
                   saved_search.email, action_type=DELETION)
        saved_search.delete()
        return HttpResponseRedirect(reverse('partner_searches')+'?company=' +
                                    str(company.id)+'&partner=' +
                                    str(partner_id))
    else:
        partner = get_object_or_404(Partner, id=partner_id, owner=company)
        contact = get_object_or_404(Contact, id=contact_id)
        log_change(contact, None, request.user, partner, contact.name,
                   action_type=DELETION)
        contact.archive()
        return HttpResponseRedirect(reverse('partner_details')+'?company=' +
                                    str(company.id)+'&partner=' +
                                    str(partner_id))


@warn_when_inactive(feature='Partner Relationship Manager is')
@company_has_access('member')
def prm_overview(request):
    """
    View that is the "Overview" of one's Partner Activity.

    """
    company, partner, user = prm_worthy(request)

    most_recent_activity = partner.get_logs()
    records = partner.get_contact_records()
    total_records = partner.get_contact_records().count()
    communication = records.order_by('-date_time')
    referrals = records.filter(contact_type='job').count()
    records = records.exclude(contact_type='job').count()
    most_recent_communication = communication[:1]
    saved_searches = partner.get_searches()
    most_recent_saved_searches = saved_searches[:1]

    ctx = {'partner': partner,
           'company': company,
           'recent_activity': most_recent_activity,
           'recent_communication': most_recent_communication,
           'recent_ss': most_recent_saved_searches,
           'count': records,
           'referrals': referrals,
           'view_name': 'PRM',
           'total_records': total_records}

    return render_to_response('mypartners/overview.html', ctx,
                              RequestContext(request))


@warn_when_inactive(feature='Partner Relationship Manager is')
@company_has_access('member')
def partner_tagging(request):
    company = get_company_or_404(request)

    tags = Tag.objects.filter(company=company).order_by('name')

    ctx = {'company': company,
           'tags': tags}

    return render_to_response('mypartners/partner_tagging.html', ctx,
                              RequestContext(request))


@warn_when_inactive(feature='Partner Relationship Manager is')
@company_has_access('member')
def edit_partner_tag(request):
    company = get_company_or_404(request)

    if request.POST:
        pk = request.GET.get('id')
        tag = Tag.objects.filter(pk=pk).first()
        form = TagForm(instance=tag, auto_id=False, data=request.POST)

        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('partner_tagging'))
        else:
            ctx = {
                'company': company,
                'form': form,
                'tag': tag
            }
            return render_to_response('mypartners/edit_tag.html', ctx,
                                      RequestContext(request))
    else:
        data = {'id': request.GET.get('id')}
        pk = request.GET.get('id')
        tag = Tag.objects.filter(pk=pk).first()
        form = TagForm(instance=tag, auto_id=False)

        ctx = {
            'company': company,
            'tag': tag,
            'form': form
        }
        return render_to_response('mypartners/edit_tag.html', ctx,
                                  RequestContext(request))


@warn_when_inactive(feature='Partner Relationship Manager is')
@company_has_access('member')
def edit_location(request):
    company, partner, _ = prm_worthy(request)
    contact = get_object_or_none(Contact, id=request.REQUEST.get('id'))
    location = get_object_or_none(
        Location, id=request.REQUEST.get('location'))

    if request.method == 'POST':
        if location:
            form = LocationForm(request.POST, instance=location)
        else:
            form = LocationForm(request.POST)

        if form.is_valid():
            location = form.save(request)

            if location not in contact.locations.all():
                contact.locations.add(location)
                contact.save()

            return HttpResponseRedirect(
                reverse('edit_contact') + "?partner=%s&id=%s" % (
                    partner.id, contact.id))
    else:
        form = LocationForm(instance=location)

    ctx = {
        'form': form,
        'company': company,
        'partner': str(partner.id),
    }
    if contact:
        ctx['contact'] = str(contact.id)
    if location:
        ctx['location'] = str(location.id)

    return render_to_response(
        'mypartners/edit_location.html', ctx, RequestContext(request))


@warn_when_inactive(feature='Partner Relationship Manager is')
@company_has_access('member')
def delete_location(request):
    company, partner, _ = prm_worthy(request)
    contact = get_object_or_404(Contact, pk=request.REQUEST.get('id', 0))
    location = get_object_or_404(
        Location, pk=request.REQUEST.get('location', 0))

    contact.locations.remove(location)

    return HttpResponseRedirect(
        reverse('edit_contact') + "?partner=%s&id=%s" % (
            partner.id, contact.id))


@warn_when_inactive(feature='Partner Relationship Manager is')
@company_has_access('member')
def delete_partner_tag(request):
    company = get_company_or_404(request)

    pk = request.GET.get('id')
    tag = Tag.objects.filter(pk=pk).first()
    tag.delete()

    return HttpResponseRedirect(reverse('partner_tagging'))


@warn_when_inactive(feature='Partner Relationship Manager is')
@company_has_access('member')
def prm_saved_searches(request):
    """
    View that lists the Partner's Saved Searches

    """
    company, partner, user = prm_worthy(request)
    saved_searches = partner.get_searches()
    saved_searches = add_pagination(request, saved_searches)
    if request.is_ajax():
        ctx = {
            'partner': partner,
            'searches': saved_searches
        }
        response = HttpResponse()
        html = render_to_response(
            'mypartners/includes/searches_column.html', ctx,
            RequestContext(request))
        response.content = html.content
        return response

    ctx = {
        'searches': saved_searches,
        'company': company,
        'partner': partner,
    }
    return render_to_response('mypartners/partner_searches.html', ctx,
                              RequestContext(request))


@warn_when_inactive(feature='Partner Relationship Manager is')
@company_has_access('member')
def prm_edit_saved_search(request):
    company, partner, user = prm_worthy(request)
    item_id = request.REQUEST.get('id')
    copy_id = request.REQUEST.get('copies')

    if item_id:
        instance = get_object_or_404(PartnerSavedSearch, id=item_id)
        form = PartnerSavedSearchForm(partner=partner, instance=instance,
                                      request=request)
    elif copy_id:
        try:
            values = PartnerSavedSearch.objects.filter(pk=copy_id).values()[0]
        except IndexError:
            # saved search to be copied doesn't exist since values is empty
            raise Http404
        else:
            values['label'] = "Copy of %s" % values['label']
            values.pop('email', None)
            values.pop('notes', None)
            values.pop('custom_message', None)
            values.pop('partner_message', None)
            form = PartnerSavedSearchForm(initial=values, partner=partner,
                                          request=request)
    else:
        form = PartnerSavedSearchForm(partner=partner, request=request)


    microsites = company.prm_saved_search_sites.values_list('domain', flat=True)
    microsites = [site.replace('http://', '').replace('https://', '').lower()
                  for site in microsites]

    ctx = {
        'company': company,
        'partner': partner,
        'item_id': item_id,
        'form': form,
        'microsites': set(microsites),
        'content_type': ContentType.objects.get_for_model(PartnerSavedSearch).id,
        'view_name': 'PRM',
    }

    return render_to_response('mypartners/partner_edit_search.html', ctx,
                              RequestContext(request))


@warn_when_inactive(feature='Partner Relationship Manager is')
@company_has_access('member')
def verify_contact(request):
    """
    Checks to see if a contact has a My.jobs account. Checks to see if they are
    active as well.

    """
    if request.REQUEST.get('action') != 'validate':
        raise Http404

    email = request.REQUEST.get('email')
    if email == 'None':
        data = {
            'status': 'None',
            'message': 'If a contact does not have an email they will not '
                       'show up on this list.',
        }
    else:
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            data = {
                'status': 'unverified',
                'message': 'A My.jobs account will be created for this '
                           'contact, which will include a personal greeting.',
            }
        else:
            # Check to see if user is active
            if user.is_active:
                data = {
                    'status': 'verified',
                    'message': '',
                }
            else:
                data = {
                    'status': 'unverified',
                    'message': 'This contact has an account on My.jobs already '
                               'but has yet to activate their account.',
                }
    return HttpResponse(json.dumps(data))


@company_has_access('member')
def partner_savedsearch_save(request):
    """
    Handles saving the PartnerSavedSearchForm and creating the inactive user
    if it is needed.

    """
    company, partner, user = prm_worthy(request)
    item_id = request.REQUEST.get('id', None)

    if item_id:
        item = get_object_or_404(PartnerSavedSearch, id=item_id,
                                 provider=company.id)
        form = PartnerSavedSearchForm(instance=item, auto_id=False,
                                      data=request.POST,
                                      partner=partner,
                                      request=request)
        if form.is_valid():
            form.save()
            return HttpResponse(status=200)
        else:
            return HttpResponse(json.dumps(form.errors))
    form = PartnerSavedSearchForm(request.POST, partner=partner,
                                  request=request)

    # Since the feed is created below, this will always be invalid.
    if 'feed' in form.errors:
        del form.errors['feed']

    if form.is_valid():
        instance = form.instance
        instance.provider = company
        instance.partner = partner
        instance.created_by = request.user
        instance.custom_message = instance.partner_message
        form.save()
        return HttpResponse(status=200)
    else:
        return HttpResponse(json.dumps(form.errors))


@warn_when_inactive(feature='Partner Relationship Manager is')
@company_has_access('member')
def partner_view_full_feed(request):
    """
    PartnerSavedSearch feed.

    """
    company, partner, user = prm_worthy(request)
    search_id = request.REQUEST.get('id')
    saved_search = get_object_or_404(PartnerSavedSearch, id=search_id)

    if company == saved_search.partnersavedsearch.provider:
        try:
            items, _ = saved_search.get_feed_items()
            items = [item for item in items if item.get('new')]
            count = len(items)
        except HTTPError:
            items = None
            count = 0
        start_date = date.today() + timedelta(get_interval_from_frequency(
            saved_search.frequency))
        extras = saved_search.partnersavedsearch.url_extras
        if extras:
            add_extra_params_to_jobs(items, extras)
            saved_search.url = add_extra_params(saved_search.url, extras)
    else:
        return HttpResponseRedirect(reverse('prm_saved_searches'))

    ctx = {
        'search': saved_search,
        'items': items,
        'view_name': 'Saved Searches',
        'is_pss': True,
        'partner': partner,
        'company': company,
        'start_date': start_date,
        'count': count,
    }

    return render_to_response('mysearches/view_full_feed.html', ctx,
                              RequestContext(request))


@warn_when_inactive(feature='Partner Relationship Manager is')
@company_has_access('member')
def prm_records(request):
    """
    ContactRecord overview and ContactRecord overview from PRM reports.

    """
    company, partner, _ = prm_worthy(request)
    _, _, contact_records = get_records_from_request(request)
    paginated_records = add_pagination(request, contact_records)

    ctx = {
        'partner': partner,
        'records': paginated_records
    }

    if request.is_ajax():
        response = HttpResponse()
        html = render_to_response(
            'mypartners/includes/contact_record_column.html', ctx,
            RequestContext(request))
        response.content = html.content
        return response

    contact_type_choices = (('all', 'All'),) + CONTACT_TYPE_CHOICES
    contact_choices = [('all', 'All')] + list(contact_records.values_list(
        'contact__name', 'contact__name').distinct().order_by('contact__name'))

    ctx.update({
        'admin_id': request.REQUEST.get('admin'),
        'company': company,
        'contact_choices': contact_choices,
        'contact_type_choices': contact_type_choices,
        'view_name': 'PRM',
    })

    return render_to_response('mypartners/main_records.html', ctx,
                              RequestContext(request))


@warn_when_inactive(feature='Partner Relationship Manager is')
@company_has_access('member')
def prm_edit_records(request):
    company, partner, user = prm_worthy(request)
    record_id = request.GET.get('id', None)

    try:
        instance = ContactRecord.objects.get(pk=record_id)
    except ContactRecord.DoesNotExist:
        instance = None

    if request.method == 'POST':
        instance = None
        if record_id:
            try:
                instance = ContactRecord.objects.get(pk=record_id)
            except ContactRecord.DoesNotExist:
                instance = None

        form = ContactRecordForm(request.POST, request.FILES,
                                 partner=partner, instance=instance)
        if form.is_valid():
            form.save(user, partner)
            search_params = request.GET.copy()
            search_params.update({'id': form.instance.pk})
            return HttpResponseRedirect(reverse('record_view') + '?' +
                                        urlencode(search_params))
    else:
        form = ContactRecordForm(partner=partner, instance=instance)

    ctx = {
        'company': company,
        'partner': partner,
        'content_type': ContentType.objects.get_for_model(ContactRecord).id,
        'item_id': record_id,
        'form': form,
    }
    return render_to_response('mypartners/edit_record.html', ctx,
                              RequestContext(request))


@warn_when_inactive(feature='Partner Relationship Manager is')
@company_has_access('member')
def prm_view_records(request):
    """
    View an individual ContactRecord.

    """
    company, partner, _ = prm_worthy(request)
    _, _, contact_records = get_records_from_request(request)
    page_number = int(request.GET.get('page', 1))
    record_id = int(request.GET.get('id', 0))

    # change number of objects per page
    paginator = Paginator(contact_records, 1)

    if record_id:
        pks = list(contact_records.values_list('pk', flat=True))

        if record_id in pks:
            page_number = pks.index(record_id) + 1
        else:
            page_number = 1
            paginator = Paginator(
                ContactRecord.objects.filter(pk=record_id), 1)

    paginated_records = paginator.page(page_number)
    record = paginated_records.object_list[0]

    attachments = record.prmattachment_set.all()
    record_history = ContactLogEntry.objects.filter(
        object_id=record.pk, content_type_id=ContentType.objects.get_for_model(
            ContactRecord).pk)

    search_params = request.GET.copy()
    navigation_params = search_params.copy()
    navigation_params.pop('id', None)

    ctx = {
        'record': record,
        'records': paginated_records,
        'partner': partner,
        'company': company,
        'attachments': attachments,
        'record_history': record_history,
        'view_name': 'PRM',
        'page': page_number,
        'search_params': urlencode(search_params),
        'navigation_params': urlencode(navigation_params)
    }

    return render_to_response('mypartners/view_record.html', ctx,
                              RequestContext(request))

@company_has_access('member')
def get_contact_information(request):
    """
    Returns a json object containing a contact's email address and
    phone number if they have one.

    """
    if request.method == "POST" and request.is_ajax():
        _, partner, _ = prm_worthy(request)

        contact_id = request.POST.get('contact') or None
        try:
            contact = Contact.objects.get(pk=contact_id)
        except Contact.DoesNotExist:
            data = {'error': 'Contact does not exist'}
            return HttpResponse(json.dumps(data))

        if partner != contact.partner:
            data = {'error': 'Permission denied'}
            return HttpResponse(json.dumps(data))

        if hasattr(contact, 'email'):
            if hasattr(contact, 'phone'):
                data = {'email': contact.email,
                        'phone': contact.phone}
            else:
                data = {'email': contact.email}
        else:
            if hasattr(contact, 'phone'):
                data = {'phone': contact.phone}
            else:
                data = {}

        return HttpResponse(json.dumps(data))
    else:
        return Http404("This view is only reachable by an AJAX POST request.")


@company_has_access('member')
def get_records(request):
    """
    Returns a json object containing the records matching the search
    criteria (contact, contact_type, and date_time range) rendered using
    records.html and the date range and date string required to update
    the time_filter.html template to match the search.

    """
    company, partner, user = prm_worthy(request)

    contact = request.REQUEST.get('contact')
    contact_type = request.REQUEST.get('record_type')

    contact = None if contact in ['all', 'undefined'] else contact
    contact_type = None if contact_type in ['all', 'undefined'] else contact_type
    dt_range, date_str, records = get_records_from_request(request)

    ctx = {
        'records': records.order_by('-date_time'),
        'company': company,
        'partner': partner,
        'contact_type': None if contact_type == 'all' else contact_type,
        'contact_name': None if contact == 'all' else contact,
        'view_name': 'PRM'
    }

    # Because javascript is going to use this, not a template,
    # convert to localtime here
    date_end = localtime(dt_range[1].replace(tzinfo=pytz.utc))
    date_start = localtime(dt_range[0].replace(tzinfo=pytz.utc))

    data = {
        'month_end': date_end.strftime('%m'),
        'day_end': date_end.strftime('%d'),
        'year_end': date_end.strftime('%Y'),
        'month_start': date_start.strftime('%m'),
        'day_start': date_start.strftime('%d'),
        'year_start': date_start.strftime('%Y'),
        'date_str': date_str,
        'html': render_to_response('mypartners/records.html', ctx,
                                   RequestContext(request)).content,
    }
    return HttpResponse(json.dumps(data))


@warn_when_inactive(feature='Partner Relationship Manager is')
@company_has_access('member')
def get_uploaded_file(request):
    """
    Determines the location of a PRMAttachment (either in S3 or in local
    storage) and redirects to it.

    PRMAttachments stored in S3 require a generated key and have a 10 minute
    access window.

    """
    company, partner, user = prm_worthy(request)
    file_id = request.GET.get('id', None)
    attachment = get_object_or_404(PRMAttachment, pk=file_id,
                                   contact_record__partner=partner)
    try:
        if repr(default_storage.connection) == 'S3Connection:s3.amazonaws.com':
            from boto.s3.connection import S3Connection

            s3 = S3Connection(settings.AWS_ACCESS_KEY_ID,
                              settings.AWS_SECRET_KEY, is_secure=True)
            path = s3.generate_url(600, 'GET',
                                   bucket=settings.AWS_STORAGE_BUCKET_NAME,
                                   key=attachment.attachment.name,
                                   force_http=True)
        else:
            path = "%s%s" % (settings.MEDIA_URL, attachment.attachment.name)
    except AttributeError:
        path = "%s%s" % (settings.MEDIA_URL, attachment.attachment.name)

    return HttpResponseRedirect(path)


@warn_when_inactive(feature='Partner Relationship Manager is')
@company_has_access('member')
def partner_main_reports(request):
    company, partner, user = prm_worthy(request)
    dt_range, date_str, records = get_records_from_request(request)

    ctx = {
        'admin_id': request.REQUEST.get('admin'),
        'partner': partner,
        'company': company,
        'contacts': records.contacts,
        'total_records': records.communication_activity.count(),
        'referral': records.referrals,
        'top_contacts': records.contacts[:3],
        'others': sum(contact['records'] for contact in records.contacts[3:]),
        'view_name': 'PRM',
        'date_start': dt_range[0],
        'date_end': dt_range[1],
        'date_display': date_str,
    }
    return render_to_response('mypartners/partner_reports.html', ctx,
                              RequestContext(request))


@company_has_access('member')
def partner_get_records(request):
    if request.method == 'GET':
        prm_worthy(request)

        dt_range, date_str, records = get_records_from_request(request)
        records = records.exclude(contact_type='job')
        email = records.filter(contact_type='email').count()
        email += records.filter(contact_type='pssemail').count()
        phone = records.filter(contact_type='phone').count()
        meetingorevent = records.filter(contact_type='meetingorevent').count()

        # figure names
        if email != 1:
            email_name = 'Emails'
        else:
            email_name = 'Email'
        if phone != 1:
            phone_name = 'Phone Calls'
        else:
            phone_name = 'Phone Call'
        if meetingorevent != 1:
            meetingorevent_name = 'Meeting or Event'
        else:
            meetingorevent_name = 'Meetings & Events'

        data = SortedDict()

        data['email'] = {"count": email, "name": email_name,
                         'typename': 'email'}
        data['phone'] = {"count": phone, "name": phone_name,
                         'typename': 'phone'}
        data['meetingorevent'] = {"count": meetingorevent,
                                  "name": meetingorevent_name,
                                  "typename": "meetingorevent"}

        return HttpResponse(json.dumps(data))
    else:
        raise Http404


@company_has_access('member')
def partner_get_referrals(request):
    if request.method == 'GET':
        prm_worthy(request)
        dt_range, date_str, records = get_records_from_request(request)

        # figure names
        if records.applications != 1:
            app_name = 'Applications'
        else:
            app_name = 'Application'
        if records.interviews != 1:
            interview_name = 'Interviews'
        else:
            interview_name = 'Interview'
        if records.hires != 1:
            hire_name = 'Hires'
        else:
            hire_name = 'Hire'

        data = {
            'applications': {'count': records.applications, 'name': app_name,
                             'typename': 'job'},
            'interviews': {'count': records.interviews, 'name': interview_name,
                           'typename': 'job'},
            'hires': {'count': records.hires, 'name': hire_name,
                      'typename': 'job'},
        }

        return HttpResponse(json.dumps(data))
    else:
        raise Http404


@warn_when_inactive(feature='Partner Relationship Manager is')
@user_passes_test(lambda u: User.objects.is_group_member(u, 'Employer'))
def prm_export(request):
    #TODO: investigate using django's builtin serialization for XML
    company, partner, user = prm_worthy(request)
    file_format = request.REQUEST.get('file_format', 'csv')
    fields = retrieve_fields(ContactRecord)
    _, _, records = get_records_from_request(request)

    if file_format == 'xml':
        root = etree.Element("contact_records")
        for record in records:
            xml_record = etree.SubElement(root, "record")
            for field in fields:
                xml = etree.SubElement(xml_record, field)
                value = getattr(record, field, '')

                if hasattr(value, 'all'):
                    value = ', '.join([val.name for val in value.all() if val])

                xml.text = contact_record_val_to_str(value)
        response = HttpResponse(etree.tostring(root, pretty_print=True,
                                               xml_declaration=True),
                                mimetype='application/force-download')
    elif file_format == 'printer_friendly':
        ctx = {
            'company': company,
            'fields': fields,
            'partner': partner,
            'records': records,
        }
        return render_to_response('mypartners/printer_friendly.html', ctx,
                                  RequestContext(request))
    # CSV/XLS
    else:
        response = HttpResponse(content_type='text/csv')
        writer = unicodecsv.writer(response, encoding='utf-8')
        writer.writerow(fields)
        for record in records:
            values = [getattr(record, field, '') for field in fields]
            values = [
                contact_record_val_to_str(v)
                if not hasattr(v, 'all') else
                ', '.join([val.name for val in v.all() if val]) for v in values
            ]
            # Remove the HTML and reformat.
            values = [strip_tags(v) for v in values]
            # replaces multiple occurences of space by a single sapce.
            values = [' '.join(filter(bool, v.split(' '))) for v in values]
            values = [re.sub('\s+\n\s+', '\n', v) for v in values]
            writer.writerow(values)

    response['Content-Disposition'] = 'attachment; ' \
                                      'filename="company_record_report".%s' \
                                      % file_format

    return response


@csrf_exempt
def process_email(request):
    """
    Creates a contact record from an email received via POST.

    """
    if request.method != 'POST':
        return HttpResponse(status=200)

    admin_email = request.REQUEST.get('from')
    headers = request.REQUEST.get('headers')
    key = request.REQUEST.get('key')
    subject = request.REQUEST.get('subject')
    email_text = request.REQUEST.get('text')
    if key != settings.EMAIL_KEY:
        return HttpResponse(status=200)
    if headers:
        parser = HeaderParser()
        headers = parser.parsestr(headers)

    if headers and 'Date' in headers:
        try:
            date_time = get_datetime_from_str(headers.get('Date'))
        except Exception:
            date_time = now()
    else:
        date_time = now()

    to = request.REQUEST.get('to', '')
    cc = request.REQUEST.get('cc', '')
    recipient_emails_and_names = getaddresses(["%s, %s" % (to, cc)])
    admin_email = getaddresses([admin_email])[0][1]
    contact_emails = filter(None,
                            [email[1] for email in recipient_emails_and_names])

    if contact_emails == [] or (len(contact_emails) == 1 and
                                contact_emails[0].lower() == 'prm@my.jobs'):
        # If prm@my.jobs is the only contact, assume it's a forward.
        fwd_headers = build_email_dicts(email_text)
        try:
            recipient_emails_and_names = fwd_headers[0]['recipients']
            contact_emails = [recipient[1] for recipient
                              in recipient_emails_and_names]
            date_time = fwd_headers[0]['date']
        except IndexError:
            contact_emails = []

    # Prevent duplicate contact records for an email address because
    # the address was in both To and CC.
    contact_emails = list(set(contact_emails))

    validated_contacts = []
    for element in contact_emails:
        if not element.lower() == 'prm@my.jobs' and validate_email(element):
            validated_contacts.append(element)

    contact_emails = validated_contacts

    try:
        contact_emails.remove(admin_email)
    except ValueError:
        pass

    admin_user = User.objects.get_email_owner(admin_email, only_verified=True)
    if admin_user is None:
        return HttpResponse(status=200)
    if admin_user.company_set.count() > 1:
        error = "Your account is setup as the admin for multiple companies. " \
                "Because of this we cannot match this email with a " \
                "specific partner on a specific company with 100% certainty. " \
                "You will need to login to My.jobs and go to " \
                "https://secure.my.jobs/prm to create your record manually."
        send_contact_record_email_response([], [], [], contact_emails,
                                           error, admin_email)
        return HttpResponse(status=200)

    partners = list(chain(*[company.partner_set.all()
                            for company in admin_user.company_set.all()]))

    possible_contacts, created_contacts, unmatched_contacts = [], [], []
    for contact in contact_emails:
        try:
            matching_contacts = Contact.objects.filter(email=contact,
                                                       partner__in=partners)
            [possible_contacts.append(x) for x in matching_contacts]
            if not matching_contacts:
                poss_partner = find_partner_from_email(partners, contact)
                if poss_partner:
                    new_contact = Contact.objects.create(name=contact,
                                                         email=contact,
                                                         partner=poss_partner)
                    change_msg = "Contact was created from email."
                    log_change(new_contact, None, admin_user,
                               new_contact.partner,   new_contact.name,
                               action_type=ADDITION, change_msg=change_msg)
                    created_contacts.append(new_contact)
                else:
                    unmatched_contacts.append(contact)
        except ValueError:
            unmatched_contacts.append(contact)

    num_attachments = int(request.POST.get('attachments', 0))
    attachments = []
    for file_number in range(1, num_attachments+1):
        try:
            attachment = request.FILES['attachment%s' % file_number]
        except KeyError:
            error = "There was an issue with the email attachments. The " \
                    "contact records for the email will need to be created " \
                    "manually."
            send_contact_record_email_response([], [], [], contact_emails,
                                               error, admin_email)
            return HttpResponse(status=200)
        attachments.append(attachment)

    created_records = []
    attachment_failures = []
    date_time = now() if not date_time else date_time
    all_contacts = possible_contacts + created_contacts
    if not all_contacts:
        error = "No contacts or contact records could be created " \
                "from this email. You will need to log in and manually " \
                "create contact records for this email."
        send_contact_record_email_response([], [], [], contact_emails,
                                           error, admin_email)
        return HttpResponse(status=200)

    for contact in all_contacts:
        change_msg = "Email was sent by %s to %s" % \
                     (admin_user.get_full_name(), contact.name)
        record = ContactRecord.objects.create(partner=contact.partner,
                                              contact_type='email',
                                              contact=contact,
                                              contact_email=contact.email,
                                              contact_phone=contact.phone,
                                              created_by=admin_user,
                                              date_time=date_time,
                                              subject=subject,
                                              notes=force_text(email_text))
        try:
            for attachment in attachments:
                prm_attachment = PRMAttachment()
                prm_attachment.attachment = attachment
                prm_attachment.contact_record = record
                setattr(prm_attachment, 'partner', contact.partner)
                prm_attachment.save()
                # The file pointer for this attachment is now at the end of the
                # file; reset it to the beginning for future use.
                attachment.seek(0)
        except AttributeError:
            attachment_failures.append(record)
        log_change(record, None, admin_user, contact.partner, contact.name,
                   action_type=ADDITION, change_msg=change_msg)

        created_records.append(record)

    send_contact_record_email_response(created_records, created_contacts,
                                       attachment_failures, unmatched_contacts,
                                       None, admin_email)
    return HttpResponse(status=200)


@company_has_access('member')
def tag_names(request):
    if request.method == 'GET':
        company = get_company_or_404(request)
        value = request.GET.get('value')
        names = list(Tag.objects.filter(
            company=company, name__icontains=value).values_list(
                'name', flat=True))
        names = sorted(
            names, key=lambda x: x if not x.startswith(value) else "-" + x)
        return HttpResponse(json.dumps(names))


@company_has_access('member')
def tag_color(request):
    if request.method == 'GET':
        company = get_company_or_404(request)
        name = request.GET.get('name')
        colors = list(Tag.objects.filter(
            company=company, name=name).values_list('hex_color', flat=True))
        return HttpResponse(json.dumps(colors))


@company_has_access('member')
def add_tags(request):
    company = get_company_or_404(request)
    data = request.GET.get('data').split(',')
    tag_get_or_create(company.id, data)
    return HttpResponse(json.dumps('success'))
