#!/usr/bin/env python

from __future__ import absolute_import, division, print_function
import socket
import requests
import logging
import traceback
import time

import settings
import json
from urllib2 import urlopen
from server import HUB_ENDPOINT, HUBS_ENDPOINT, PROJECTS_ENDPOINT, DATA_ENDPOINT
from urllib import quote_plus

SLEEP_WAIT_SEC = 60 # 1 minute


def get_uuid():
    """
    Return the UUID of this hub for use in communication with server
    """
    return socket.gethostname()

def register_hub():
    """
    Registers current computer as a hub
    Note - hub must be defined in the server (lookup by hostname)
    :return:
    """
    hub_name = socket.gethostname()


def send_hub_ip():
    """
    Updates the hub's IP on the server side
    :return:
    """
    hostname = socket.gethostname()
    encoded_hostname = quote_plus(hostname)
    try:
        my_ip = json.load(urlopen('http://jsonip.com'))['ip']
    except Exception as e:
        s = traceback.format_exc()
        logger.error('Error getting IP: {} {}'.format(e,s))
        my_ip = '0.0.0.0'

    logger.info("Updating IP for {} ({}) : {}".format(hostname,encoded_hostname,my_ip))
    try:
        data = {
            'ip_address': my_ip,
        }

        logger.debug("Sending update to server: {}".format(data))
        response = requests.patch(HUB_ENDPOINT(encoded_hostname), data=data)
        if response.ok is False:
            raise Exception('Server sent a {} status code instead of 200: {}'.format(response.status_code,
                                                                                         response.text))
        else:
            logger.debug("Done")
    except Exception as e:
        logger.error('Error sending updated badge into to server: {}'.format(e))


def sending_loop():
    """
    Continuously send update IP
    :return:
    """
    while True:
        send_hub_ip()
        time.sleep(SLEEP_WAIT_SEC)


def _read_hubs_list_from_server(logger, retry=True, retry_delay_sec=5):
    """
    Reads hubs info from the server
    :param retry: if blocking is set, hub will keep retrying
    :return:
    """
    server_hubs = {}
    done = False

    while not done:
        try:
            logger.info("Requesting devices from server...")
            response = requests.get(HUBS_ENDPOINT)
            if response.ok:
                logger.info("Updating hubs list ({})...".format(len(response.json())))
                for d in response.json():
                    server_hubs[d.get('uuid')] = d
                done = True
            else:
                raise Exception('Got a {} from the server'.format(response.status_code))

        except (requests.exceptions.ConnectionError, Exception) as e:
            s = traceback.format_exc()
            logger.error("Error reading hubs list from server : {} {}".format(e,s))
            if not retry:
                done = True
            else:
                logger.info("Sleeping for {} seconds before retrying".format(retry_delay_sec))
                time.sleep(retry_delay_sec)

    return server_hubs


def pull_hubs_list(logger):
    server_hubs = _read_hubs_list_from_server(logger, retry=False)
    return server_hubs

def _get_project_id(logger):
    headers = {
        "X-HUB-UUID": socket.gethostname(),
        "X-APPKEY": settings.APPKEY
    }
    
    resp = requests.request("GET", PROJECTS_ENDPOINT, headers=headers)
    if resp.status_code == 200:
        return resp.json()["key"]
    else:
        #TODO what do
        #I don't think this is likely to ever happen, at least
        logger.error("Error getting project key from server, status code: {}"
            .format(resp.status_code))

def send_data_to_server(logger, data_type, data):
    """
    Send data to the server
    Args:
        logger: for logging events/errors
        data_type: audio or proximity
        data: a json array containing the data to send
    Returns:
         the number of chunks written on the server
    Raises:
        RequestException: raises if the status code indicates an http error
    """
    project_id = _get_project_id(logger)
    headers = {
        "content-type": "application/json",
        "X-HUB-UUID": get_uuid(),
        "X-APPKEY": settings.APPKEY
    }
    payload = {
        "data_type": data_type,
        "chunks": data
    }
    url = DATA_ENDPOINT(project_id) 
    response = requests.request("POST", url, data=json.dumps(payload), headers=headers)
    response.raise_for_status() 
    return response.json()["chunks_written"]

if __name__ == "__main__":
    register_hub()
    logging.basicConfig()
    logger = logging.getLogger('badge_server')
    logger.setLevel(logging.INFO)
    sending_loop()
