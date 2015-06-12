import boto
from boto.route53 import Route53Connection
from boto.route53.zone import Zone
from boto.route53.exception import DNSServerError
import DNS

from django.conf import settings


class EfficientRoute53Connection(Route53Connection):
    def get_hosted_zone_by_name(self, hosted_zone_domain):
        """
        Gets hosted zone details for matching domain without pulling all
        hosted zones.

        Amazon API documentation:
        http://docs.aws.amazon.com/Route53/latest/APIReference/api-list-hosted-zones-by-name-private.html

        """
        hosted_zone_domain = "%s." % hosted_zone_domain
        uri = ('{version}/hostedzonesbyname?dnsname={domain}&'
               'maxitems=1'.format(version=self.Version,
                                   domain=hosted_zone_domain))
        response = self.make_request('GET', uri)
        body = response.read()
        boto.log.debug(body)
        if response.status >= 300:
            raise DNSServerError(response.status,
                                 response.reason,
                                 body)
        e = boto.jsonresponse.Element(list_marker='HostedZones',
                                      item_marker=('HostedZone',))
        h = boto.jsonresponse.XmlHandler(e, None)
        h.parse(body)
        zones = e['ListHostedZonesByNameResponse']['HostedZones']
        if not zones:
            return None
        zone = zones[0]
        if zone.Name == hosted_zone_domain:
            return self.get_hosted_zone(zone['Id'].split('/')[-1])

    def get_hosted_zone(self, zone_id):
        """
        Gets hosted zone details for matchign zone_id without pulling all
        hosted zones.

        Amazon API documentation:
        http://docs.aws.amazon.com/Route53/latest/APIReference/API-get-hosted-zone-private.html

        """
        uri = '{version}/hostedzone/{zone_id}'.format(version=self.Version,
                                                      zone_id=zone_id)
        response = self.make_request('GET', uri)
        body = response.read()
        boto.log.debug(body)
        if response.status >= 300:
            raise DNSServerError(response.status,
                                 response.reason,
                                 body)
        e = boto.jsonresponse.Element(item_marker=('HostedZone',))
        h = boto.jsonresponse.XmlHandler(e, None)
        h.parse(body)
        return e


def domain_exists(domain):
    """
    Confirms that we own a domain.

    """
    connection = EfficientRoute53Connection(settings.AWS_ACCESS_KEY_ID,
                                            settings.AWS_SECRET_KEY)
    zone = connection.get_hosted_zone_by_name(domain)
    return bool(zone)


def can_send_email(domain):
    """
    Confirms that we own the domain and there's an mx record pointing
    to sendgrid for it.

    Inputs:
    :domain: Domain to be checked

    Outputs:
    :return: Boolean/None
        None: we don't control this domain
        False: we control this domain but no MX record has been created
        True: we control this domain and an MX record already exists
    """
    if not domain_exists(domain):
        return None

    DNS.DiscoverNameServers()
    mx_hosts = DNS.mxlookup(domain)
    return any(mx_host == 'mx.sendgrid.net' for _, mx_host in mx_hosts)


def make_mx_record(domain):
    """
    Makes an mx record for a domain that we own.

    :return: The status returned from the add_mx call if it was successful.
    """
    if not domain_exists(domain):
        return None
    connection = EfficientRoute53Connection(settings.AWS_ACCESS_KEY_ID,
                                            settings.AWS_SECRET_KEY)
    zone = connection.get_hosted_zone_by_name(domain)
    if zone:
        zone = Zone(connection, zone['GetHostedZoneResponse']['HostedZone'])

    return zone.add_mx(domain , ['10 mx.sendgrid.net'])