from django.core.urlresolvers import reverse


def success_url(request):
    # We specify a nexturl for pages that require login and pages that should
    # redirect back to themselves.
    if request.REQUEST.get('next'):
        return request.REQUEST.get('next')

    # So if we didn't specify the url, redirect to the homepage.
    return reverse('home')
