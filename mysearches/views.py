import json
from datetime import datetime
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponse
from django.template import RequestContext
from django.shortcuts import render_to_response, get_object_or_404

from mysearches.models import SavedSearch
from mysearches.forms import SavedSearchForm
from mysearches.helpers import *

@login_required
def saved_search_form(request):
    if request.method == "POST":
        form = SavedSearchForm(user=request.user, data=request.POST)
        if request.POST.get('action', None) == 'validate' :
            rss_url = validate_dotjobs_url(request.POST['url'])
            if rss_url:
               feed_title = get_feed_title(rss_url)
               data = {'rss_url': rss_url,
                       'feed_title': feed_title,
                       'url_status': 'valid'
               }
            else:
                data = {'url_status': 'not valid'}
            return HttpResponse(json.dumps(data))
        else:
            if form.is_valid():
                form.save()
                return HttpResponseRedirect('/saved-search')
    else:
        form = SavedSearchForm(user=request.user)
        
    return render_to_response('mysearches/saved_search_form.html',
                              {'form':form}, RequestContext(request))

@login_required
def saved_search_main(request):
    saved_searches = SavedSearch.objects.filter(user=request.user)
    return render_to_response('mysearches/saved_search_main.html',
                              {'saved_searches': saved_searches},
                              RequestContext(request))

@login_required
def view_full_feed(request, search_id):
    saved_search = SavedSearch.objects.get(id=search_id)
    if request.user == saved_search.user:
        rss_soup = get_rss_soup(saved_search.feed)
        items = parse_rss_chunk(rss_soup)
        frequency = saved_search.get_verbose_frequency()
        date = datetime.today().date()
        label = saved_search.label
        return render_to_response('mysearches/view_full_feed.html',
                                  {'label': label,
                                   'frequency': frequency,
                                   'items': items},
                                  RequestContext(request))
    else:
        return HttpResponseRedirect('/saved-search')
