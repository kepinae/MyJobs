from functools import partial, wraps

from django.core.urlresolvers import reverse
from django.conf import settings
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext

from myjobs.models import User
from universal.helpers import build_url, get_company


def company_has_access(perm_field):
    """
    Determines whether or not a user and their current company has access to
    the requested feature.

    inputs:
        :perm_field: The name of the BooleanField on Company that handles
            permissions for the requested feature.
    """
    def decorator(view_func):
        def wrap(request, *args, **kwargs):

            # If the user is not logged in, redirect them to the login page
            # with this url as the next url.
            if request.user.is_anonymous():
                params = {'next': request.get_full_path()}
                next_url = build_url(reverse('login'), params)
                return HttpResponseRedirect(next_url)

            # If the user is logged in, but they aren't a CompanyUser or they
            # are a CompanyUser, but their current Company doesn't have
            # perm_field access, return a 404.
            company = get_company(request)

            if not company or (perm_field and not getattr(company, perm_field,
                                                          False)):
                raise Http404

            return view_func(request, *args, **kwargs)
        return wraps(view_func)(wrap)
    return decorator

def company_in_sitepackages(view_func):
    """
    Raises an Http404 exception if the wrapped view is accessed by a user who
    isn't a member of a company who owns a site package which includes the
    current seo site.

    That is, if John is visiting testing.jobs, which is in a site package owned
    by DirectEmployers, but John isn't a company user for DirectEmployers, he
    will see a 404 page.
    """
    @wraps(view_func)
    def wrap(request, *args, **kwargs):
        if not request.user.is_anonymous() and not request.user.can_access_site(
                settings.SITE):
            raise Http404

        return view_func(request, *args, **kwargs)
    return wrap


def activate_user(view_func):
    """
    Activates the user for a given request if it is not already active. The
    main use case for this is password resets, where the user must be active
    to successfully submit the request.
    """
    @wraps(view_func)
    def wrap(request, *args, **kwargs):
        if request.method == 'POST':
            email = request.POST.get('email', None)
            if email is not None:
                user = User.objects.get_email_owner(email)
                if user is not None and not user.is_active:
                    user.is_active = True
                    user.deactivate_type = 'none'
                    user.save()
        return view_func(request, *args, **kwargs)
    return wrap


# Rather than write a few different decorators, I decided to go with a
# decorator factory and write partials to handle repetitive cases.
def warn_when(condition, feature, message, link=None, link_text=None,
              exception=None, redirect=True):
    """
    A decorator which displays a warning page for :feature: with :message: when
    the :condition: isn't met. If a :link: is provided, a button with that link
    will displayed, showing :link_text: or "OK".

    Inputs:
    :condition: a callable that takes the request object and returns a boolean.
    :feature: The feature for which the warning is being displayed.
    :message: A helpful message to display to the user.
    :link: A link to use for the optional button that appears after the
           message.
    :link_text: The text to appear on the button when "OK" is to generic.
    """

    def decorator(view_func):
        @wraps(view_func)
        def wrap(request, *args, **kwargs):
            if request.user.is_anonymous() and redirect:
                params = {'next': request.get_full_path()}
                next_url = build_url(reverse('login'), params)
                return HttpResponseRedirect(next_url)

            ctx = {'feature': feature,
                   'message': message,
                   'link': link,
                   'link_text': link_text}

            if condition(request):
                if exception:
                    raise exception('{0}: {1}'.format(feature, message))

                return render_to_response('warning_page.html',
                                          ctx,
                                          RequestContext(request))

            return view_func(request, *args, **kwargs)
        return wrap
    return decorator

not_found_when = partial(
    warn_when,
    exception=Http404)

# TODO: refactor these so that warn_when/not_found_when can be passed in,
# rather than having a separate function for each one.
warn_when_inactive = partial(
    warn_when,
    condition=lambda req:
        not req.user.is_anonymous() and
        (not req.user.is_verified or not req.user.is_active),
    message='You have yet to activate your account.',
    link='/accounts/register/resend',
    link_text='Resend Activation')
