import os
import re
import uuid

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.core.cache import cache
from django.core.files.storage import default_storage
from django.db import models, DatabaseError
from django.db.models.signals import post_save
from django.dispatch import receiver


def get_location(link_type, filename):
    filename, extension = os.path.splitext(filename)
    filename = '.'.join([re.sub(r'[\W]', '', filename),
                         re.sub(r'[\W]', '', extension)])

    if not filename or filename == '.':
        filename = 'unnamed_file'

    uid = uuid.uuid4()
    location_template = '/social-icons/%s/%s/%s'
    if (getattr(settings, 'DEFAULT_FILE_STORAGE') !=
            'storages.backends.s3boto.S3BotoStorage'):
        location_template = 'files/' + location_template
    location = location_template % (uid, link_type.site, filename)
    while default_storage.exists(location):
        uid = uuid.uuid4()
        location = location_template % (uid, link_type.site, filename)
    return location


class SocialLinkType(models.Model):
    def __unicode__(self):
        return self.site

    def delete(self, *args, **kwargs):
        filename = self.icon.name
        super(SocialLinkType, self).delete(*args, **kwargs)
        default_storage.delete(filename)


    @classmethod
    def icon_choices(cls):
        choices = cls.LINK_ICON_CHOICES
        try:
            choices += tuple(SocialLinkType.objects.values_list('icon', 'site'))
        except DatabaseError:
            pass
        return choices

    def save(self, *args, **kwargs):
        super(SocialLinkType, self).save(*args, **kwargs)
        try:
            if repr(default_storage.connection) == 'S3Connection:s3.amazonaws.com':
                from boto import connect_s3, s3
                conn = connect_s3(settings.AWS_ACCESS_KEY_ID,
                                  settings.AWS_SECRET_KEY)
                bucket = conn.create_bucket(settings.AWS_STORAGE_BUCKET_NAME)
                key = s3.key.Key(bucket)
                key.key = self.icon.name
                key.set_acl('public-read')
        except AttributeError:
            pass

    LINK_ICON_CHOICES = (
        ("//d2e48ltfsb5exy.cloudfront.net/content_ms/files/company-social-icon.png", 'Default'),
        ("//d2e48ltfsb5exy.cloudfront.net/content_ms/files/facebook.png", 'Facebook'),
        ("//d2e48ltfsb5exy.cloudfront.net/content_ms/files/flickr.png", 'Flickr'),
        ("//d2e48ltfsb5exy.cloudfront.net/content_ms/files/linkedin.png", 'LinkedIn'),
        ("//d2e48ltfsb5exy.cloudfront.net/content_ms/files/twitter.png", 'Twitter'),
        ("//d2e48ltfsb5exy.cloudfront.net/content_ms/files/youtube.png", 'Youtube'),
        ("//d2e48ltfsb5exy.cloudfront.net/content_ms/files/de-icon.png", 'Directemployers'),
        ("//d2e48ltfsb5exy.cloudfront.net/content_ms/files/dj-icon.png", '.jobs')
    )

    site = models.CharField(max_length=60, unique=True)
    icon = models.FileField(upload_to=get_location, max_length=767)


class SocialLink(models.Model):
    def __unicode__(self):
        return self.link_title

    def get_icon(self):
        """
        Returns the canonical link for this social icon. Prepends our
        cloudfront url if the link_icon is custom.

        Outputs:
        :link_icon: Full, protocol-relative link to this icon
        """
        link_icon = self.link_icon
        s3_url = '//d2e48ltfsb5exy.cloudfront.net'
        png_url = 'http://png.nlx.org'
        if (getattr(settings, 'DEFAULT_FILE_STORAGE') ==
                'storages.backends.s3boto.S3BotoStorage'):
            if not link_icon.startswith((s3_url, png_url)):
                # We're in a production environment uploading icons to s3
                # and this icon was manually uploaded; Prepend s3 url to it
                link_icon = s3_url + link_icon
        else:
            site = Site.objects.get(pk=settings.SITE_ID)
            link_icon = '/'.join([site.domain, link_icon])
        return link_icon
    
    def show_sites(self):
        return ", ".join(self.sites.all().values_list('domain', flat=True))

    LINK_TYPE_CHOICES = (
        ('company', 'Company'),
        ('social', 'Social'),
        ('directemployers', 'DirectEmployers'),
    )

    link_url = models.URLField()
    link_title = models.CharField(max_length=60, db_index=True)
    link_type = models.CharField(max_length=255, choices=LINK_TYPE_CHOICES)
    link_icon = models.CharField(max_length=255,
                                 default='default')
    sites = models.ManyToManyField('seo.SeoSite')
    group = models.ForeignKey('auth.Group', null=True)
    content_type = models.ForeignKey(ContentType)


class MicrositeCarousel(models.Model):
    def __unicode__(self):
        return 'Microsite Carousel:%s' % int(self.id)
    
    def show_active_sites(self):
        return ", ".join(self.seosite_set.all().values_list('domain', flat=True))
    
    is_active = models.BooleanField('Active', default=False)
    include_all_sites = models.BooleanField('Include All Group\'s Sites',
                                            default=False)
    group = models.ForeignKey('auth.Group', null=True)
    # sites to be included as links in the carousel
    link_sites = models.ManyToManyField('seo.SeoSite',
                                        related_name='linked_carousel',
                                        blank=True)
    display_rows = models.IntegerField('Display Rows', choices=[(1,1), (2,2),
                                                                (3,3), (4,4),
                                                                (5,5), (6,6),
                                                                (7,7), (8,8)])
    carousel_title = models.CharField('Carousel Title', max_length=200,
                                      null=True, blank=True)

@receiver(post_save, sender=SocialLink)
def clear_slink_cache(sender, **kwargs):
    instance = kwargs['instance']
    sites = instance.sites.all()

    for site in sites:
        key = "%s:social_links" % site.domain
        cache.delete(key)
