import datetime
import json

from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth import logout as log_out
from django.contrib.auth.views import password_reset
from django.contrib.auth.decorators import user_passes_test
from django.http import Http404, HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from django.views.generic import TemplateView
from myjobs.decorators import user_is_allowed
from myjobs.helpers import expire_login
from registration.models import ActivationProfile
from registration.forms import RegistrationForm
from myblocks.models import Page
from myblocks.views import BlockView
from myjobs.models import User
from myprofile.models import SecondaryEmail
from myprofile.forms import (InitialNameForm, InitialAddressForm,
                             InitialPhoneForm, InitialEducationForm,
                             InitialWorkForm)
from registration.forms import CustomPasswordResetForm


# New in Django 1.5. Class based template views for static pages
class RegistrationComplete(TemplateView):
    template_name = 'registration/registration_complete.html'


def register(request):
    """
    Registration form. Creates inactive user (which in turn sends an activation
    email) and redirect to registration complete page.

    """
    form = RegistrationForm()
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            new_user = User.objects.create_user(request=request,
                                                **form.cleaned_data)
            username = form.cleaned_data['email']
            password = form.cleaned_data['password1']
            user = authenticate(username=username, password=password)
            expire_login(request, user)
            return HttpResponseRedirect('/accounts/register/complete/')
    return HttpResponse(json.dumps({'errors': form.errors.items()}))


@user_is_allowed()
def resend_activation(request):
    template = 'registration/%s/resend_activation.html' % settings.PROJECT
    activation = ActivationProfile.objects.get_or_create(
        user=request.user, email=request.user.email)[0]
    activation.send_activation_email()
    return render_to_response(template,
                              context_instance=RequestContext(request))


@user_is_allowed()
def activate(request, activation_key, invitation=False):
    """
    Activates user and returns a boolean to activated. Activated is passed
    into the template to display an appropriate message if the activation
    passes or fails.

    Inputs:
    :activation_key: string representing an activation key for a user
    """
    logged_in = True
    if request.user.is_anonymous():
        logged_in = False
    activated = ActivationProfile.objects.activate_user(activation_key)

    name_form = InitialNameForm(prefix="name")
    education_form = InitialEducationForm(prefix="edu")
    phone_form = InitialPhoneForm(prefix="ph")
    work_form = InitialWorkForm(prefix="work")
    address_form = InitialAddressForm(prefix="addr")

    ctx = {'activated': activated,
           'logged_in': logged_in,
           'name_form': name_form,
           'phone_form': phone_form,
           'address_form': address_form,
           'work_form': work_form,
           'education_form': education_form,
           'num_modules': len(settings.PROFILE_COMPLETION_MODULES)}

    if invitation:
        if activated is False and not request.user.is_anonymous():
            activated = request.user
            ctx['activated'] = activated

        if activated is not False:
            if activated.in_reserve:
                activated.in_reserve = False
                password = User.objects.make_random_password()
                activated.set_password(password)
                activated.save()
                ctx['password'] = password
    template = 'registration/%s/activate.html' % settings.PROJECT
    return render_to_response(template, ctx,
                              context_instance=RequestContext(request))


@user_passes_test(User.objects.not_disabled)
def merge_accounts(request, activation_key):
    AP = ActivationProfile
    template = 'registration/%s/merge_request.html' % settings.PROJECT

    ctx = {'merged': False}

    # Check if activation key exists
    if not AP.objects.filter(activation_key=activation_key).exists():
        return render_to_response(template, ctx,
                                  context_instance=RequestContext(request))

    # Get activation key and associated user
    activation_profile = AP.objects.get(activation_key=activation_key)
    existing_user = request.user
    new_user = activation_profile.user

    # Check if the activation request is expired
    if activation_profile.activation_key_expired():
        return render_to_response(template, ctx,
                                  context_instance=RequestContext(request))

    # Create a secondary email
    SecondaryEmail.objects.create(user=existing_user, label='Merged Email',
                                  email=activation_profile.email, verified=True,
                                  verified_date=datetime.datetime.now())

    # Update the contacts
    for contact in new_user.contact_set.all():
        contact.user = existing_user
        contact.save()

    # Update the saved searches
    for search in new_user.savedsearch_set.all():
        search.user = existing_user
        search.save()

    for status in new_user.status_set.all():
        status.approved_by = existing_user
        status.save()


    # Remove the new user and activation profile
    activation_profile.delete()
    new_user.delete()
    ctx['merged'] = True
    return render_to_response(template, ctx,
                              context_instance=RequestContext(request))


def logout(request):
    log_out(request)
    response = redirect('home')
    if 'myguid' in request.COOKIES:
        response.delete_cookie(key='myguid', domain='.my.jobs')
    return response


class DseoLogin(BlockView):
    page_type = Page.LOGIN

    def set_page(self, request):
        """
        Override set_page to remove default option, allowing us to
        prevent login on some sites.

        """
        if request.user.is_authenticated() and request.user.is_staff:
            try:
                page = Page.objects.filter(sites=settings.SITE,
                                           status=Page.STAGING,
                                           page_type=self.page_type)[0]
                setattr(self, 'page', page)
                return page
            except IndexError:
                pass

        try:
            page = Page.objects.filter(sites=settings.SITE,
                                       status=Page.PRODUCTION,
                                       page_type=self.page_type)[0]
        except IndexError:
            raise Http404
        setattr(self, 'page', page)
        return page


def custom_password_reset(request):
    template = 'registration/%s/password_reset_form.html' % settings.PROJECT
    email_domain = 'my.jobs'
    if getattr(settings, 'SITE', None):
        email_domain = settings.SITE.email_domain

    from_email = settings.EMAIL_FORMATS[settings.FORGOTTEN_PASSWORD]['address']
    from_email = from_email.format(domain=email_domain.lower())

    return password_reset(request,  password_reset_form=CustomPasswordResetForm,
                          from_email=from_email, template_name=template)
