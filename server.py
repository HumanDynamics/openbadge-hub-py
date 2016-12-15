# Defining end points for backend-server
from __future__ import absolute_import, division, print_function
import settings

SERVER = 'http://'+settings.BADGE_SERVER_ADDR+':'+settings.BADGE_SERVER_PORT+'/'
PROJECTS_ENDPOINT = '{}projects'.format(SERVER)
BADGES_ENDPOINT = '{}badges/'.format(SERVER)
HUBS_ENDPOINT = '{}hubs/'.format(SERVER)
# can't use the string format method because reasons
DATALOGS_ENDPOINT = SERVER + "{}/datalogs"

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
    return DATALOGS_ENDPOINT.format(x)

BADGE_ENDPOINT = _badge
DATA_ENDPOINT = _data
HUB_ENDPOINT = _hub
