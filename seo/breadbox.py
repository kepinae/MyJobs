from django.core.urlresolvers import reverse, reverse_lazy
from django.conf import settings
from django.template.loader import render_to_string

from seo import helpers


class Breadbox(object):
    """
    Builds and contains breadcrumbs.

    """
    class Breadcrumb(object):
        """
        An object containing a url with either a part of the path or a
        query_dict parameter removed and a human readable display_title
        that describes the section that was removed.

        """
        def __init__(self, display_title='', url=reverse_lazy('view_jobs'),
                     breadcrumb_class='breadcrumb_bread_box'):
            self.url = url
            self.display_title = display_title
            self.breadcrumb_class = breadcrumb_class

    def __init__(self, path, filters, jobs, query_dict):
        self.path = path
        self.filters = filters
        self.jobs = jobs
        self.job_count = 0
        self.query_dict = query_dict

        # Set defaults for the breadcrumb types so that the functions that
        # create them aren't responsible for guaranteeing their existance.
        self.custom_facet_breadcrumbs = []
        self.location_breadcrumbs = []
        self.moc_breadcrumbs = []

        self.q_breadcrumb = None
        self.company_breadcrumb = None
        self.title_breadcrumb = None
        self.clear_breadcrumb = None

        self.build_breadcrumbs()

    def _make_clear_breadcrumb(self):
        if not self.clear_breadcrumb:
            kwargs = {
                'display_title': "Clear All",
                'url': reverse('all_jobs'),
            }
            self.clear_breadcrumb = self.Breadcrumb(**kwargs)

    def _make_url(self, path=None, query_dict=None):
        """
        Builds a url using either self.path/self.query_dict or the specified
        path/query_dict.

        :param path: The path you want the new url to contain. if None
                     it uses self.path.
        :param query_dict: The query dict you want the new url to contain.
                           If None it uses self.query_dict.
        :return: A new url, built from self.path or the new specified path
                 and self.query_dict or a specified query_dict.

        """
        path = path if path is not None else self.path
        if path == '/' or not path:
            path = reverse('all_jobs')
        query_dict = query_dict if query_dict is not None else self.query_dict
        query_string = query_dict.urlencode()
        return "%s?%s" % (path, query_string) if query_string else path

    def _remove_param_from_query_dict(self, param):
        """
        :param param: Param to remove from self.query_dict.
        :return: A new QueryDict with param removed.

        """
        query_dict = self.query_dict.copy()
        if param in query_dict:
            del query_dict[param]
        return query_dict

    def all_breadcrumbs(self):
        """
        :return: A list of all the breadcrumbs in the Breadbox.

        """
        breadcrumbs = (self.custom_facet_breadcrumbs +
                       self.location_breadcrumbs + self.moc_breadcrumbs)
        single_breadcrumbs = [self.title_breadcrumb, self.company_breadcrumb,
                              self.clear_breadcrumb, self.q_breadcrumb]
        for breadcrumb in single_breadcrumbs:
            if breadcrumb:
                breadcrumbs.append(breadcrumb)
        return breadcrumbs

    def build_breadcrumbs(self):
        """
        Builds all possible breadrcrumbs for a Breadbox.

        """
        self.build_filter_breadcrumbs()
        self.build_param_breadcrumbs()

    def build_breadcrumb_for_slug_type(self, slug_type, display_title):
        """
        Builds a breadcrumb for a specific slug_type. Useful for slugs
        that will only have a single breadcrumb.

        :param slug_type: The slug type of the breadcrumb you're building.
                          It's a string that matches the * in *_slug.
                          Possible types can be found in settings.SLUG_TAGS.
        :param display_title: The display title you want the resulting
                              breadcrumb to have.
        :return: A breadcrumb.

        """
        ending_slug = settings.SLUG_TAGS[slug_type].strip('/')
        breadcrumb_class = slug_type.replace('_slug', '_bread_box')

        if self.filters.get(slug_type):
            slug = self.filters[slug_type].strip('/')
            path_for_slug = "/%s/%s" % (slug, ending_slug)
            new_path = self.path.replace(path_for_slug, '')
            kwargs = {
                'breadcrumb_class': breadcrumb_class,
                'display_title': display_title,
                'url': self._make_url(path=new_path)
            }
            return self.Breadcrumb(**kwargs)
        return None

    def build_breadcrumb_for_param(self, param):
        """
        Builds a breadcrumb for a specific param. Useful for params that
        will have only a single breadcrumb.

        :param param: The query_dict param you would like to build a
                      breadcrumb for.
        :return: A breadcrumb.

        """
        param_value = self.query_dict.get(param)
        if param_value:
            updated_query_dict = self._remove_param_from_query_dict(param)
            updated_url = self._make_url(query_dict=updated_query_dict)
            kwargs = {
                'breadcrumb_class': '%s_bread_box' % param,
                'url': updated_url,
                'display_title': param_value,
            }
            return self.Breadcrumb(**kwargs)

    def build_company_breadcrumbs_from_slugs(self):
        company_slug_value = self.filters.get('company_slug')
        display_title = helpers.bread_box_company_heading(company_slug_value)
        breadcrumb = self.build_breadcrumb_for_slug_type('company_slug',
                                                         display_title)
        if breadcrumb:
            self.company_breadcrumb = breadcrumb
            self._make_clear_breadcrumb()

    def build_custom_facet_breadcrumbs_from_slugs(self):
        ending_slug = settings.SLUG_TAGS['facet_slug']
        if self.filters.get('facet_slug'):
            facet_filters = self.filters['facet_slug'].strip('/')
            facet_filters = facet_filters.split('/')
            custom_facets = helpers.standard_facets_by_name_slug(facet_filters)

            # If there's at most one path that we can remove, then
            # remove the ending slug as well.
            new_path = self.path
            if len(custom_facets) < 2:
                new_path = new_path.replace(ending_slug, '')

            self.custom_facet_breadcrumbs = []
            for facet in custom_facets:
                path_for_facet = new_path.replace("/%s" % facet.name_slug, '')
                kwargs = {
                    'breadcrumb_class': 'facet_bread_box',
                    'display_title': facet.name,
                    'url': self._make_url(path=path_for_facet)
                }
                self.custom_facet_breadcrumbs.append(self.Breadcrumb(**kwargs))
                self._make_clear_breadcrumb()

    def build_filter_breadcrumbs(self):
        """
        Builds all the breadcrumbs related to slugs.

        """
        self.build_company_breadcrumbs_from_slugs()
        self.build_custom_facet_breadcrumbs_from_slugs()
        self.build_location_breadcrumbs_from_slugs()
        self.build_moc_breadcrumbs_from_slugs()
        self.build_title_breadcrumbs_from_slugs()

    def build_location_breadcrumbs_from_slugs(self):
        ending_slug = settings.SLUG_TAGS['location_slug'].strip('/')

        if self.filters.get('location_slug'):
            location_slug = self.filters['location_slug'].strip('/')
            display_title = helpers.bread_box_location_heading(location_slug,
                                                               jobs=self.jobs)
            location_filters = location_slug.split('/')
            location_filters = filter(lambda x: x != 'none', location_filters)

            new_path = self.path

            # If there's only a country then we can safely remove the
            # ending slug as well.
            slugs = new_path.split('/')
            if ending_slug in slugs and len(location_filters) < 2:
                slugs.remove(ending_slug)

            location_slugs = location_slug.split('/')
            try:
                left = slugs.index(location_slugs[0])
            except ValueError:
                # location slug isn't part of the path 
                pass
            else:
                right = left + len(location_slugs)
                new_path = '/'.join(slugs[:left] + location_filters[1:] +
                                    slugs[right:])

            kwargs = {
                # This class name is different because of the way we used to
                # do the location breadbox.
                'breadcrumb_class': 'loc_up_bread_box',
                'display_title': display_title,
                'url': self._make_url(path=new_path)
            }
            self.location_breadcrumbs = [self.Breadcrumb(**kwargs)]
            self._make_clear_breadcrumb()

    def build_location_breadcrumbs_from_params(self):
        location = self.build_breadcrumb_for_param('location')
        if location:
            self.location_breadcrumbs = [location]
            self._make_clear_breadcrumb()

    def build_moc_breadcrumbs_from_params(self):
        moc = self.build_breadcrumb_for_param('moc')
        if moc:
            self.moc_breadcrumbs = [moc]
            self._make_clear_breadcrumb()

    def build_moc_breadcrumbs_from_slugs(self):
        moc_slug_value = self.filters.get('moc_slug')
        display_title = helpers.bread_box_moc_heading(moc_slug_value)

        breadcrumb = self.build_breadcrumb_for_slug_type('moc_slug',
                                                         display_title)
        if breadcrumb:
            self.moc_breadcrumbs = [breadcrumb]
            self._make_clear_breadcrumb()

    def build_param_breadcrumbs(self):
        """
        Builds all the breadcrumbs related to the query dict.

        """
        self.build_location_breadcrumbs_from_params()
        self.build_moc_breadcrumbs_from_params()
        self.build_q_breadcrumbs_from_params()

    def build_q_breadcrumbs_from_params(self):
        q = self.build_breadcrumb_for_param('q')
        if q:
            self.q_breadcrumb = q
            self._make_clear_breadcrumb()

    def build_title_breadcrumbs_from_slugs(self):
        title_slug_value = self.filters.get('title_slug')
        display_title = helpers.bread_box_title_heading(title_slug_value,
                                                        jobs=self.jobs)
        breadcrumb = self.build_breadcrumb_for_slug_type('title_slug',
                                                         display_title)
        if breadcrumb:
            self.title_breadcrumb = breadcrumb
            self._make_clear_breadcrumb()

    def company_display_heading(self):
        if self.company_breadcrumb:
            return self.company_breadcrumb.display_title
        return ''

    def custom_facet_display_heading(self):
        # A large number of our facets end in " Jobs", but when we chain the
        # facets titles together the " Jobs" ending for each individual
        # facet doesn't make sense anymore, so strip it out and then
        # re-add it after all the facet titles have been composed.
        display_titles = []
        for facet in self.custom_facet_breadcrumbs:
            title = facet.display_title
            if title.endswith(' Jobs'):
                title = title[:-5]
            display_titles.append(title)
        heading = ' and '.join(display_titles)
        return "%s Jobs" % heading if heading else ''

    def location_display_heading(self):
        if self.location_breadcrumbs:
            # Right now we shouldn't have multiple locations, so
            # just take the first one. In the future if we do have
            # multiple locations the contents of
            # breadbox.location_breadcrumbs.display_title can easily be 'ORed'
            # together.
            return self.location_breadcrumbs[0].display_title
        return ''

    def moc_display_heading(self):
        if self.moc_breadcrumbs:
            # Right now we shouldn't have multiple mocs, so
            # just take the first one. In the future if we do have
            # multiple mocs the contents of
            # breadbox.moc_breadcrumbs.display_title can easily be 'ORed'
            # together.
            return self.moc_breadcrumbs[0].display_title
        return ''

    def q_display_heading(self):
        if self.q_breadcrumb:
            return self.q_breadcrumb.display_title
        return ''

    def title_display_heading(self):
        if self.title_breadcrumb and self.title_breadcrumb.display_title:
            return "%s Jobs" % self.title_breadcrumb.display_title
        return ''

    def render(self):
        """
        Renders the Breadbox as a string. Not currently used in templates
        because of the generous use of mark_safe that it would require,
        but useful for testing.

        :return: The Breadbox rendered as a string.

        """
        return render_to_string('includes/breadbox.html', {'breadbox': self})
