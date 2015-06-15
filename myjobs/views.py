import base64
import datetime
import json
import logging
import urllib2
from urlparse import urlparse
import uuid

from django.conf import settings
from django.contrib.auth import logout, authenticate
from django.contrib.auth.decorators import user_passes_test
from django.db import IntegrityError
from django.forms import Form, model_to_dict
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response, redirect, render, Http404
from django.template import RequestContext
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView

from captcha.fields import ReCaptchaField

from universal.helpers import get_domain
from myjobs.decorators import user_is_allowed
from myjobs.forms import ChangePasswordForm, EditCommunicationForm
from myjobs.helpers import expire_login, log_to_jira, get_title_template
from myjobs.models import Ticket, User, FAQ, CustomHomepage
from myprofile.forms import (InitialNameForm, InitialEducationForm,
                             InitialAddressForm, InitialPhoneForm,
                             InitialWorkForm)
from myprofile.models import ProfileUnits, Name
from registration.forms import RegistrationForm, CustomAuthForm
from tasks import process_sendgrid_event

logger = logging.getLogger('__name__')


class About(TemplateView):
    template_name = "about.html"


class Privacy(TemplateView):
    template_name = "privacy-policy.html"


class Terms(TemplateView):
    template_name = "terms.html"


class CaptchaForm(Form):
    captcha = ReCaptchaField(label="", attrs={'theme': 'white'})


def error_500(request):
    response = render(request, "500.html")
    response.status_code = 500
    return response


def home(request):
    """
    The home page view receives 2 separate Ajax requests, one for the
    registration form and another for the initial profile information form. If
    everything checks out alright and the form saves with no errors, it returns
    a simple string, 'valid', as an HTTP Response, which the front end
    recognizes as a signal to continue with the account creation process. If an
    error occurs, this triggers the jQuery to update the page. The form
    instances with errors must be passed back to the form template it was
    originally from.

    """
    registration_form = RegistrationForm(auto_id=False)
    login_form = CustomAuthForm(auto_id=False)

    name_form = InitialNameForm(prefix="name")
    education_form = InitialEducationForm(prefix="edu")
    phone_form = InitialPhoneForm(prefix="ph")
    work_form = InitialWorkForm(prefix="work")
    address_form = InitialAddressForm(prefix="addr")
    nexturl = request.GET.get('next')
    title_template = get_title_template(nexturl)
    if nexturl:
        nexturl = urllib2.unquote(nexturl)
        nexturl = urllib2.quote(nexturl.encode('utf8'))

    last_ms = request.COOKIES.get('lastmicrosite')
    site_name = ''
    logo_url = ''
    show_registration = True
    if last_ms:
        try:
            last_ms = get_domain(last_ms)
            custom_page = CustomHomepage.objects.get(domain=last_ms)
            logo_url = custom_page.logo_url
            show_registration = custom_page.show_signup_form
            site_name = custom_page.name

        except CustomHomepage.DoesNotExist:
            pass

    data_dict = {'num_modules': len(settings.PROFILE_COMPLETION_MODULES),
                 'registrationform': registration_form,
                 'loginform': login_form,
                 'name_form': name_form,
                 'phone_form': phone_form,
                 'address_form': address_form,
                 'work_form': work_form,
                 'education_form': education_form,
                 'nexturl': nexturl,
                 'logo_url': logo_url,
                 'show_registration': show_registration,
                 'site_name': site_name,
                 'logo_template': title_template,
                 }

    if request.method == "POST":
        if request.POST.get('action') == "register":
            registration_form = RegistrationForm(request.POST, auto_id=False)
            if registration_form.is_valid():
                new_user, created = User.objects.create_user(
                    request=request,
                    send_email=True,
                    **registration_form.cleaned_data)
                user_cache = authenticate(
                    username=registration_form.cleaned_data['email'],
                    password=registration_form.cleaned_data['password1'])
                expire_login(request, user_cache)
                # pass in gravatar url once user is logged in. Image generated
                # on AJAX success
                html = render_to_response('includes/account-page-2.html',
                                          data_dict, RequestContext(request))
                data = {'gravatar_url': new_user.get_gravatar_url(size=100),
                        'html': html.content}
                response = HttpResponse(json.dumps(data))
                response.set_cookie('myguid', new_user.user_guid,
                                    expires=365*24*60*60, domain='.my.jobs')
                return response
            else:
                return HttpResponse(json.dumps(
                    {'errors': registration_form.errors.items()}))

        elif request.POST.get('action') == "login":
            login_form = CustomAuthForm(data=request.POST)
            if login_form.is_valid():
                expire_login(request, login_form.get_user())

                url = request.POST.get('nexturl')

                # Boolean for activation login page to show initial forms
                # again or not
                has_units = False
                if len(login_form.get_user().profileunits_set.all()) > 0:
                    has_units = True

                response_data = {
                    'validation': 'valid', 'url': url,
                    'units': has_units,
                    'gravatar_url': login_form.get_user().get_gravatar_url(
                        size=100)}
                response = HttpResponse(json.dumps(response_data))
                response.set_cookie('myguid', login_form.get_user().user_guid,
                                    expires=365*24*60*60, domain='.my.jobs')
                return response
            else:
                return HttpResponse(json.dumps({'errors':
                                                login_form.errors.items()}))

        elif request.POST.get('action') == "save_profile":
            name_form = InitialNameForm(request.POST, prefix="name",
                                        user=request.user)
            if not name_form.changed_data:
                name_form = InitialNameForm(prefix="name")

            education_form = InitialEducationForm(request.POST, prefix="edu",
                                                  user=request.user)
            if not education_form.changed_data:
                education_form = InitialEducationForm(prefix="edu")

            phone_form = InitialPhoneForm(request.POST, prefix="ph",
                                          user=request.user)
            if not phone_form.changed_data:
                phone_form = InitialPhoneForm(prefix="ph")

            work_form = InitialWorkForm(request.POST, prefix="work",
                                        user=request.user)
            if not work_form.changed_data:
                work_form = InitialWorkForm(prefix="work")

            address_form = InitialAddressForm(request.POST, prefix="addr",
                                              user=request.user)
            if not address_form.changed_data:
                address_form = InitialAddressForm(prefix="addr")

            forms = [name_form, education_form, phone_form, work_form,
                     address_form]
            valid_forms = [form for form in forms if form.is_valid()]
            invalid_forms = []
            for form in forms:
                if form.changed_data and not form.is_valid():
                    invalid_forms.append(form)

            if not invalid_forms:
                for form in valid_forms:
                    if form.changed_data:
                        form.save(commit=False)
                        form.user = request.user
                        form.save_m2m()
                return HttpResponse('valid')
            else:
                return render_to_response('includes/initial-profile-form.html',
                                          {'name_form': name_form,
                                           'phone_form': phone_form,
                                           'address_form': address_form,
                                           'work_form': work_form,
                                           'education_form': education_form},
                                          context_instance=RequestContext(
                                              request))

    return render_to_response('index.html', data_dict, RequestContext(request))


def contact_faq(request):
    """
    Grabs FAQ and orders them by alphabetical order on question.

    """
    faq = FAQ.objects.filter(is_visible=True).order_by('question')
    if not faq.count() > 0:
        return HttpResponseRedirect(reverse('contact'))
    data_dict = {'faq': faq}
    return render_to_response('contact-faq.html', data_dict, RequestContext(request))


def contact(request):
    if request.POST:
        name = request.POST.get('name')
        contact_type = request.POST.get('type')
        reason = request.POST.get('reason')
        from_email = request.POST.get('email')
        phone_num = request.POST.get('phone')
        comment = request.POST.get('comment')
        form = CaptchaForm(request.POST)
        if form.is_valid():
            components = []
            component_ids = {'My.jobs Error': {'id': '12903'},
                             'Job Seeker': {'id': '12902'},
                             'Employer': {'id': '12900'},
                             'Partner': {'id': '12901'},
                             'Request Demo': {'id': '13900'}}
            if component_ids.get(reason):
                components.append(component_ids.get(reason))
            components.append(component_ids.get(contact_type))
            issue_dict = {
                'summary': '%s - %s' % (reason, from_email),
                'description': '%s' % comment,
                'issuetype': {'name': 'Task'},
                'customfield_10400': str(name),
                'customfield_10401': str(from_email),
                'customfield_10402': str(phone_num),
                'components': components}

            subject = 'Contact My.jobs by a(n) %s' % contact_type
            body = """
                   Name: %s
                   Is a(n): %s
                   Email: %s

                   %s
                   """ % (name, contact_type, from_email, comment)

            to_jira = log_to_jira(subject, body, issue_dict, from_email)
            if to_jira:
                time = datetime.datetime.now().strftime(
                    '%A, %B %d, %Y %l:%M %p')
                return HttpResponse(json.dumps({'validation': 'success',
                                                'name': name,
                                                'c_type': contact_type,
                                                'reason': reason,
                                                'c_email': from_email,
                                                'phone': phone_num,
                                                'comment': comment,
                                                'c_time': time}))
            else:
                return HttpResponse('success')
        else:
            return HttpResponse(json.dumps({'validation': 'failed',
                                            'errors': form.errors.items()}))
    else:
        form = CaptchaForm()
        data_dict = {'form': form}
    return render_to_response('contact.html', data_dict,
                              RequestContext(request))


@user_is_allowed()
@user_passes_test(User.objects.not_disabled)
def edit_account(request):
    user = request.user
    obj = User.objects.get(id=user.id)
    change_password = False

    if user.is_verified:
        communication_form = EditCommunicationForm(user=user, instance=obj)
    else:
        communication_form = None
    password_form = ChangePasswordForm(user=user)

    if request.user.password_change:
        change_password = True

    ctx = {
        'user': user,
        'communication_form': communication_form,
        'password_form': password_form,
        'change_password': change_password,
    }

    if request.method == "POST":
        obj = User.objects.get(id=request.user.id)
        if 'communication' in request.REQUEST:
            form = EditCommunicationForm(user=request.user, instance=obj,
                                         data=request.POST)
            if form.is_valid():
                form.save()
                ctx['communication_form'] = form
                ctx['message_body'] = ('Communication Settings have been '
                                       'updated successfully.')
                ctx['messagetype'] = 'success'
                template = '%s/edit-account.html' % settings.PROJECT
                return render_to_response(template, ctx,
                                          RequestContext(request))
            else:
                ctx['communication_form'] = form
                template = '%s/edit-account.html' % settings.PROJECT
                return render_to_response(template, ctx,
                                          RequestContext(request))

        elif 'password' in request.REQUEST:
            form = ChangePasswordForm(user=request.user, data=request.POST)
            if form.is_valid():
                request.user.password_change = False
                request.user.save()
                form.save()
                ctx['password_form'] = form
                ctx['message_body'] = ('Password Settings have been '
                                       'updated successfully.')
                ctx['messagetype'] = 'success'
                template = '%s/edit-account.html' % settings.PROJECT
                return render_to_response(template, ctx,
                                          RequestContext(request))
            else:
                ctx['password_form'] = form
                template = '%s/edit-account.html' % settings.PROJECT
                return render_to_response(template, ctx,
                                          RequestContext(request))
        else:
            return Http404

    return render_to_response('%s/edit-account.html' % settings.PROJECT, ctx,
                              RequestContext(request))


@user_passes_test(User.objects.not_disabled)
def delete_account(request):
    email = request.user.email
    request.user.delete()

    template = '%s/delete-account-confirmation.html' % settings.PROJECT
    ctx = {'email': email}

    return render_to_response(template, ctx, RequestContext(request))


@user_passes_test(User.objects.not_disabled)
def disable_account(request):
    user = request.user
    email = user.email
    user.disable()
    logout(request)

    template = '%s/disable-account-confirmation.html' % settings.PROJECT
    ctx = {'email': email}

    return render_to_response(template, ctx, RequestContext(request))


@csrf_exempt
def batch_message_digest(request):
    """
    Used by SendGrid to POST batch events.

    Accepts a POST request containing a batch of events from SendGrid. A batch
    of events is a series of JSON strings separated by new lines (Version 1 and
    2) or as well formed JSON (Version 3)

    Creates a celery task that adds these events to the EmailLog.

    """
    if 'HTTP_AUTHORIZATION' in request.META:
        method, details = request.META['HTTP_AUTHORIZATION'].split()
        if method.lower() == 'basic':
            # login_info is intended to be a base64-encoded string in the
            # format "email:password" where email is a urlquoted string
            login_info = base64.b64decode(details).split(':')
            if len(login_info) == 2:
                login_info[0] = urllib2.unquote(login_info[0])
                user, password = login_info

                if (user == settings.SENDGRID_BATCH_POST_USER and
                        password == settings.SENDGRID_BATCH_POST_PASSWORD):

                    process_sendgrid_event.delay(request.body)
                    return HttpResponse(status=200)
    return HttpResponse(status=403)


@user_is_allowed(pass_user=True)
def continue_sending_mail(request, user=None):
    """
    Updates the user's last response time to right now.
    Allows the user to choose to continue receiving emails if they are
    inactive.
    """
    user = user or request.user
    user.last_response = datetime.date.today()
    user.save()
    return redirect('/')


def check_name_obj(user):
    """
    Utility function to process and return the user name object.

    Inputs:
    :user:  request.user object

    Returns:
    :initial_dict: Dictionary object with updated name information
    """
    initial_dict = model_to_dict(user)
    try:
        name = Name.objects.get(user=user, primary=True)
    except Name.DoesNotExist:
        name = None
    if name:
        initial_dict.update(model_to_dict(name))
    return initial_dict


@user_is_allowed(pass_user=True)
def unsubscribe_all(request, user=None):
    user = user or request.user
    user.opt_in_myjobs = False
    user.save()

    return render_to_response('myjobs/unsubscribe_all.html',
                              context_instance=RequestContext(request))


def toolbar(request):
    user = request.user
    if not user or user.is_anonymous():
        # Ensure that old myguid cookies can be handled correctly
        guid = request.COOKIES.get('myguid', '').replace('-', '')
        try:
            user = User.objects.get(user_guid=guid)
        except User.DoesNotExist:
            pass
    if not user or user.is_anonymous():
        data = {"user_fullname": "",
                "user_gravatar": "",
                "employer": ""}
    else:
        try:
            name = user.get_full_name()
            if not name:
                name = user.email
        except ProfileUnits.DoesNotExist:
            name = user.email
        employer = (True if user.groups.filter(name='Employer')
                    else False)
        data = {"user_fullname": (("%s..." % name[:17]) if len(name) > 20
                                  else name),
                "user_gravatar": user.get_gravatar_url(),
                "employer": employer}
    callback = request.GET.get('callback', '')
    response = '%s(%s);' % (callback, json.dumps(data))
    response = HttpResponse(response, content_type="text/javascript")
    caller = request.REQUEST.get('site', '')
    if caller and not caller.endswith('www.my.jobs'):
        max_age = 30 * 24 * 60 * 60
        last_name = request.REQUEST.get('site_name', caller)
        response.set_cookie(key='lastmicrosite',
                            value=caller,
                            max_age=max_age,
                            domain='.my.jobs')
        response.set_cookie(key='lastmicrositename',
                            value=last_name,
                            max_age=max_age,
                            domain='.my.jobs')
    return response


def cas(request):
    redirect_url = request.GET.get('redirect_url', 'http://www.my.jobs/')
    user = request.user

    if not user or user.is_anonymous():
        guid = request.COOKIES.get('myguid')
        try:
            user = User.objects.get(user_guid=guid)
        except User.DoesNotExist:
            pass
    if not user or user.is_anonymous():
        response = redirect("https://secure.my.jobs/?next=%s" %
                            redirect_url)
    else:
        ticket = Ticket()
        try:
            ticket.ticket = uuid.uuid4()
            ticket.session_id = request.session.session_key
            ticket.user = request.user
            ticket.save()
        except IntegrityError:
            return cas(request)
        except Exception, e:
            logging.error("cas: %s" % e)
            response = redirect("https://secure.my.jobs/?next=%s" %
                                redirect_url)
        else:
            if '?' in redirect_url:
                response = redirect("%s&ticket=%s&uid=%s" %
                                    (redirect_url, ticket.ticket,
                                     ticket.user.user_guid))
            else:
                response = redirect("%s?ticket=%s&uid=%s" %
                                    (redirect_url, ticket.ticket,
                                     ticket.user.user_guid))
    caller = urlparse(redirect_url)
    try:
        page = CustomHomepage.objects.get(domain=caller.netloc.split(":")[0])
        response.set_cookie(key='lastmicrosite',
                                value="%s://%s" % (caller.scheme,
                                                   caller.netloc),
                                max_age=30 * 24 * 60 * 60,
                                domain='.my.jobs')
        response.set_cookie(key='lastmicrositename',
                                value=page.name,
                                max_age=30 * 24 * 60 * 60,
                                domain='.my.jobs')
    except CustomHomepage.DoesNotExist:
        pass

    return response


def topbar(request):
    callback = request.REQUEST.get('callback')
    user = request.user

    if not user or user.is_anonymous():
        # Ensure that old myguid cookies can be handled correctly
        guid = request.COOKIES.get('myguid', '').replace('-', '')
        try:
            user = User.objects.get(user_guid=guid)
        except User.DoesNotExist:
            pass

    if not user or user.is_anonymous():
        user = None

    ctx = {'user': user}

    response = HttpResponse(content_type='text/javascript')

    caller = request.REQUEST.get('site', '')
    if caller:
        max_age = 30 * 24 * 60 * 60
        last_name = request.REQUEST.get('site_name', caller)
        response.set_cookie(key='lastmicrosite',
                            value=caller,
                            max_age=max_age,
                            domain='.my.jobs')
        response.set_cookie(key='lastmicrositename',
                            value=last_name,
                            max_age=max_age,
                            domain='.my.jobs')

    html = render_to_response('includes/topbar.html', ctx,
                              RequestContext(request))

    response.content = "%s(%s)" % (callback, json.dumps(html.content))

    return response

