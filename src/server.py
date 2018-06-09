# Defining end points for backend-server
from __future__ import absolute_import, division, print_function
import settings
import time
import netifaces
import json

SERVER = 'http://'+settings.BADGE_SERVER_ADDR+':'+settings.BADGE_SERVER_PORT+'/'
PROJECTS_ENDPOINT = '{}projects'.format(SERVER)
BADGES_ENDPOINT = '{}badges/'.format(SERVER)
HUBS_ENDPOINT = '{}hubs/'.format(SERVER)
BEACONS_ENDPOINT = '{}beacons/'.format(SERVER)
DATAFILES_ENDPOINT = "{}{}".format(SERVER, "{}/datafiles")


def _badge(x):
    """
    Generates endpoint for a given badge
    :param x:
    :return:
    """
    return '{}{}/'.format(BADGES_ENDPOINT, x)

def _beacon(x):
    """
    Generates endpoint for a given beacon
    :param x:
    :return:
    """
    return '{}{}/'.format(BEACONS_ENDPOINT, x)


def _hub(x):
    """
    Generates endpoint for a given hub
    :param x: hostname of the hub
    :return:
    """
    return '{}{}/'.format(HUBS_ENDPOINT, x)


def _data(x):
    """
    Generates endpoint for a given hub
    :param x: project key of hub's project
    :return:
    """
    return DATAFILES_ENDPOINT.format(x)

BADGE_ENDPOINT = _badge
BEACON_ENDPOINT = _beacon
DATA_ENDPOINT = _data
HUB_ENDPOINT = _hub


def get_ips():
    """
    Generates a JSON string with the list of IPs used by the hub
    :return:
    """
    interfaces = netifaces.interfaces()
    ips=[]
    for i in interfaces:
        if i == 'lo':
            continue
        iface = netifaces.ifaddresses(i).get(netifaces.AF_INET)
        if iface is not None:
            for j in iface:
                ips.append({i:j['addr']})

    ips_json = json.dumps(ips)
    return ips_json


def request_headers():
    """ 
    Generate the headers to be used for all requests to server
    Note - all items must be strings
    """
    print(get_ips())
    return {
        "X-APPKEY": settings.APPKEY,
        "X-HUB-UUID": settings.HUB_UUID,
        "X-HUB-TIME": str(time.time()),
        "X-ALL-IPS": get_ips()
    }
