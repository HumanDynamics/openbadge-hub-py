from __future__ import absolute_import, division, print_function
import os
import re
import logging
import requests
from server import BEACON_ENDPOINT, BEACONS_ENDPOINT, request_headers
from badge import Badge,now_utc_epoch
from settings import DATA_DIR, LOG_DIR, CONFIG_DIR

devices_file = CONFIG_DIR + 'devices_beacon.txt'


class BeaconManagerStandalone():
    def __init__(self, logger,timestamp):
        self._beacons= None
        self.logger = logger
        self._device_file = devices_file

        if timestamp:
            self._init_ts = timestamp
            self._init_ts_fract = 0
        else:
            self._init_ts, self._init_ts_fract = now_utc_epoch()
            self._init_ts -= 5 * 60 # start pulling data from the 5 minutes
        logger.debug("Standalone version. Will request data since {} {}".format(self._init_ts,self._init_ts_fract))

    def _read_file(self,device_file):
        """
        refreshes an internal list of devices included in device_macs.txt
        Format is device_mac<space>badge_id<space>project_id<space>device_name
        :param device_file:
        :return:
        """
        if not os.path.isfile(device_file):
            self.logger.error("Cannot find devices file: {}".format(device_file))
            exit(1)
        self.logger.info("Reading devices from file: {}".format(device_file))

        #extracting badge id, project id and mac address
        with open(device_file, 'r') as devices_macs:

            badge_project_ids =[]
            devices = []

            for line in devices_macs:
                    if not line.lstrip().startswith('#'):
                        device_details = line.split()
                        devices.append(device_details[0])
                        badge_project_ids.append(device_details[1:3])
                    
        
        #mapping badge id and project id to mac address
        mac_id_map = {}    
        for i in range(len(devices)):
            mac_id_map[devices[i]] = badge_project_ids[i]
        
        for d in devices:
            self.logger.debug("    {}".format(d))

        beacons = {mac: Badge(mac,
                                       self.logger,
                                       key=mac,  # using mac as key since no other key exists
                                       badge_id=int(mac_id_map[mac][0]),
                                       project_id=int(mac_id_map[mac][1]),
                                       ) for mac in mac_id_map.keys()    
                        }

        return beacons

    def pull_beacons_list(self):
        # first time we read as is
        if self._beacons is None:
            file_beacons = self._read_file(self._device_file)
            self._beacons = file_beacons
        else:
            # update list
            file_beacons = self._read_file(self._device_file)
            for mac in file_beacons:
                if mac not in self._beacons:
                    # new badge
                    self.logger.debug("Found new badge in file: {}".format(mac))
                    self._beacons[mac] = file_beacons[mac]

    def pull_beacon(self, mac):
        """
        Contacts to server (if responding) and updates the given pull_beacon data
        :param mac:
        :return:
        """
        pass # not implemented

    def send_beacon(self, mac):
        """
        Sends timestamps of the given beacon to the server
        :param mac:
        :return:
        """
        pass # not implemented in standalone

    def create_beacon(self, name, mac , beacon_id ,project_id):
        """
        Creates a beacon using the giving information
        :param name: user name
        :param mac: beacon mac
        :param beacon_id: beacon_id
        :param project_id: project_id
        :return:
        """
        self.logger.debug("Command 'create_beacon' is not implemented for standalone mode'")
        pass # not implemented in standalone

    @property
    def beacons(self):
        if self._beacons is None:
            raise Exception('Beacons list has not been initialized yet')
        return self._beacons


if __name__ == "__main__":
    logging.basicConfig()
    logger = logging.getLogger('beacon_server')
    logger.setLevel(logging.DEBUG)

    mgr = BeaconManagerStandalone(logger=logger,timestamp=1520270000)
    mgr.pull_beacons_list()
    print(mgr.beacons)
