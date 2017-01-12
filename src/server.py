# Defining end points for backend-server
from __future__ import absolute_import, division, print_function
import settings
import time

SERVER = 'http://'+settings.BADGE_SERVER_ADDR+':'+settings.BADGE_SERVER_PORT+'/'
PROJECTS_ENDPOINT = '{}projects'.format(SERVER)
BADGES_ENDPOINT = '{}badges/'.format(SERVER)
HUBS_ENDPOINT = '{}hubs/'.format(SERVER)
DATAFILES_ENDPOINT = "{}{}".format(SERVER, "{}/datafiles")

def _badge(x):
    """
    Generates endpoint for a given badge
    :param x:
    :return:
    """
    return '{}{}/'.format(BADGES_ENDPOINT, x)


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
DATA_ENDPOINT = _data
HUB_ENDPOINT = _hub

def request_headers():
    """ 
    Generate the headers to be used for all requests to server
    """
    return {
        "X-APPKEY": settings.APPKEY,
        "X-HUB-UUID": settings.HUB_UUID,
        "X-HUB-TIME": time.time()
    }
