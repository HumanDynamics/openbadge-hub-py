from __future__ import absolute_import, division, print_function
import requests
import time

from badge import *
from settings import APPKEY, HUB_UUID
from server import BEACON_ENDPOINT, BEACONS_ENDPOINT, request_headers
import traceback


class BeaconManagerServer:
    DEFAULT_TIMEOUT = (9.05, 15)

    def __init__(self, logger):
        self._beacons = None
        self.logger = logger


    def _jason_beacon_to_object(self, d):
        conv = lambda x: int(float(x))
        return Badge(d.get('badge'),
                    self.logger,
                    d.get('key'),
                    badge_id = d.get('id'),
                    project_id = d.get('advertisement_project_id'),
                    init_voltage=d.get('last_voltage')
        )

    def _read_beacons_list_from_server(self, retry=True, retry_delay_sec=5):
        """
        Reads beacons info from the server
        :param retry: if blocking is set, hub will keep retrying
        :return:
        """
        server_beacons = {}
        done = False

        while not done:
            try:
                self.logger.info("Requesting devices from server...")
                response = requests.get(BEACONS_ENDPOINT, headers=request_headers(), timeout=self.DEFAULT_TIMEOUT)
                if response.ok:
                    self.logger.info("Updating beacons list ({})...".format(len(response.json())))
                    for d in response.json():
                        if(d.get('active')==True):
                            server_beacons[d.get('badge')] = self._jason_beacon_to_object(d)
                    done = True
                else:
                    raise Exception('Got a {} from the server'.format(response.status_code))

            except (requests.exceptions.ConnectionError, Exception) as e:
                s = traceback.format_exc()
                self.logger.error("Error reading beacon list from server : {}, {}".format(e,s))
                if not retry:
                    done = True
                else:
                    self.logger.info("Sleeping for {} seconds before retrying".format(retry_delay_sec))
                    time.sleep(retry_delay_sec)

        return server_beacons

    def _read_beacon_from_server(self, beacon_key, retry=False, retry_delay_sec=5):
        """
        Reads given beacon info from the server
        :param retry: if blocking is set, hub will keep retrying
        :return:
        """
        done = False

        while not done:
            try:
                self.logger.info("Requesting device {} from server...".format(beacon_key))
                response = requests.get(
                    BEACON_ENDPOINT(beacon_key), headers=request_headers(), timeout=self.DEFAULT_TIMEOUT)
                if response.ok:
                    #self.logger.debug("Received ({})...".format(response.json()))
                    return self._jason_beacon_to_object(response.json())
                else:
                    raise Exception('Got a {} from the server'.format(response.status_code))

            except (requests.exceptions.ConnectionError, Exception) as e:
                self.logger.error("Error reading badge from server : {}".format(e))
                if not retry:
                    done = True
                else:
                    self.logger.info("Sleeping for {} seconds before retrying".format(retry_delay_sec))
                    time.sleep(retry_delay_sec)

        return None

    def pull_beacons_list(self):
        self._beacons = self._read_beacons_list_from_server(retry=True)

    def pull_beacon(self, mac):
        """
        Contacts to server (if responding) and updates the given beacon data
        :param mac:
        :return:
        """
        raise NotImplementedError()

    def send_beacon(self, mac):
        """
        Sends timestamps of the given beacon to the server
        :param mac:
        :return:
        """
        try:
            beacon = self._beacons[mac]
            data = {
                'observed_id' : beacon.observed_id,
                'last_voltage': beacon.last_voltage,
                'last_seen_ts': beacon.last_seen_ts,
            }

            self.logger.debug("Sending update beacon data to server, beacon {} : {}".format(beacon.key, data))
            response = requests.patch(
                BEACON_ENDPOINT(beacon.key), data=data, headers=request_headers(), timeout=self.DEFAULT_TIMEOUT)
            if response.ok is False:
                if response.status_code == 400:
                    self.logger.debug("Server had more recent date, beacon {} : {}".format(beacon.key, response.text))
                else:
                    raise Exception('Server sent a {} status code instead of 200: {}'.format(response.status_code,
                                                                                         response.text))
        except Exception as e:
            self.logger.error('Error sending updated beacon info to server: {}'.format(e))

    def create_beacon(self, name, mac , beacon_id ,project_id):
        """
        Creates a beacon using the giving information
        :param name: user name
        :param mac: beacon mac
        :param beacon_id: beacon_id
        :param project_id: project_id
        :return:
        """
        try:
            data = {
                'name': name,
                'badge': mac,
                'id': beacon_id,
                'project_id':project_id,
            }

            self.logger.info("Creating new beacon : {}".format(data))
            response = requests.post(
                BEACONS_ENDPOINT, data=data, headers=request_headers(), timeout=self.DEFAULT_TIMEOUT)
            if response.ok is False:
                s = traceback.format_exc()
                raise Exception('Error creating beacon {}. Status: {}, Error: {}, {}'.format(data, response.status_code,
                                                                                             response.text, s))
        except Exception as e:
            s = traceback.format_exc()
            self.logger.error('Error creating new beacon. Error: {} ,{}'.format(e,s))

    @property
    def beacons(self):
        if self._beacons is None:
            raise Exception('Beacons list has not been initialized yet')
        return self._beacons
